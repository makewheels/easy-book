"""Agents SDK 适配层测试（离线）：FunctionTool 包装与 BookTools.execute 的衔接。"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from book_agent import assistant as assistant_mod
from book_agent.assistant import _TracedModel, build_agent_tools
from book_agent.schema import ALL_TOOLS
from book_agent.tools import BookTools


def test_function_tools_match_all_tools():
    ftools = build_agent_tools(BookTools(api_url="http://localhost:1"))
    assert len(ftools) == len(ALL_TOOLS) == 21
    assert [t.name for t in ftools] == [t["function"]["name"] for t in ALL_TOOLS]


def test_invoke_routes_through_execute_with_write_gate():
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    ftools = {t.name: t for t in build_agent_tools(tools)}

    # 写操作未确认：返回 requiresConfirmation（不发网络请求）
    result = asyncio.run(ftools["create_student"].on_invoke_tool(None, json.dumps({"name": "测试"})))
    parsed = json.loads(result)
    assert parsed["requiresConfirmation"] is True
    assert parsed["planned"] == {"name": "测试"}

    # 工具执行记录照常进入 trace
    assert tools.trace[-1]["tool"] == "create_student"


def test_invoke_unknown_args_still_returns_json():
    tools = BookTools(api_url="http://localhost:1")
    ftools = {t.name: t for t in build_agent_tools(tools)}
    result = asyncio.run(ftools["search_students"].on_invoke_tool(None, ""))
    parsed = json.loads(result)
    # 空参数调 search 会尝试请求 localhost:1 → 错误转返回值，仍是合法 JSON
    assert isinstance(parsed, dict)


def test_traced_model_records_system_prompt(monkeypatch):
    """SDK 把系统提示词作为独立参数传给模型，generation 上报必须显式带上它。"""
    captured: dict = {}
    monkeypatch.setattr(
        assistant_mod.lf_trace,
        "start_generation",
        lambda *, name, model, messages: captured.update(messages=messages) or object(),
    )
    monkeypatch.setattr(assistant_mod.lf_trace, "finish_generation", lambda *a, **k: None)

    class _FakeInner:
        async def get_response(self, *args, **kwargs):
            return SimpleNamespace(output=None, usage=None)

    traced = _TracedModel(_FakeInner(), "test-model")
    asyncio.run(traced.get_response("SYS_PROMPT", [{"role": "user", "content": "hi"}], None, []))

    assert captured["messages"][0] == {"role": "system", "content": "SYS_PROMPT"}
    assert captured["messages"][1] == {"role": "user", "content": "hi"}


def test_traced_model_without_system_prompt_keeps_input(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        assistant_mod.lf_trace,
        "start_generation",
        lambda *, name, model, messages: captured.update(messages=messages) or object(),
    )
    monkeypatch.setattr(assistant_mod.lf_trace, "finish_generation", lambda *a, **k: None)

    class _FakeInner:
        async def get_response(self, *args, **kwargs):
            return SimpleNamespace(output=None, usage=None)

    traced = _TracedModel(_FakeInner(), "test-model")
    user_items = [{"role": "user", "content": "hi"}]
    asyncio.run(traced.get_response(None, user_items, None, []))

    assert captured["messages"] == user_items


# ── HTTP 层完整请求/响应记录 ───────────────────────────────────


def test_snapshot_request_drops_absent_and_transport_keys():
    class Omit:  # 模拟 openai SDK 的 Omit sentinel
        pass

    snap = assistant_mod._snapshot_request(
        {
            "model": "qwen3-max",
            "messages": [{"role": "user", "content": "hi"}],
            "tools": [{"type": "function", "function": {"name": "t"}}],
            "temperature": None,  # 空值过滤
            "stream": Omit(),  # sentinel 过滤
            "extra_headers": {"X": "1"},  # 传输层，不属于请求体
            "extra_query": {"q": "1"},
            "extra_body": {"k": "v"},  # extra_body 属于请求体，保留
        }
    )
    assert snap == {
        "model": "qwen3-max",
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{"type": "function", "function": {"name": "t"}}],
        "extra_body": {"k": "v"},
    }


def test_instrument_client_records_full_request_and_response(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        assistant_mod.lf_trace,
        "record_generation_request",
        lambda *, request: captured.update(req=request),
    )
    monkeypatch.setattr(
        assistant_mod.lf_trace,
        "record_generation_response",
        lambda *, response: captured.update(resp=response),
    )

    class _FakeCompletions:
        def __init__(self):
            self.calls = []

        async def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(model_dump=lambda mode=None: {"echo": kwargs["messages"]})

    completions = _FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    instrumented = assistant_mod._instrument_client(client)
    resp = asyncio.run(
        instrumented.chat.completions.create(
            model="qwen3-max",
            messages=[{"role": "system", "content": "SYS"}, {"role": "user", "content": "hi"}],
            tools=[{"type": "function", "function": {"name": "search_students"}}],
            temperature=None,
            extra_headers={"Authorization": "Bearer ***"},
        )
    )

    # 请求快照：model/messages/tools 一字不少，空值与传输层参数不进记录
    assert captured["req"]["model"] == "qwen3-max"
    assert captured["req"]["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "hi"},
    ]
    assert captured["req"]["tools"][0]["function"]["name"] == "search_students"
    assert "temperature" not in captured["req"]
    assert "extra_headers" not in captured["req"]
    # 响应快照来自 model_dump，原样透传给调用方
    assert captured["resp"] == {"echo": [{"role": "system", "content": "SYS"}, {"role": "user", "content": "hi"}]}
    assert len(completions.calls) == 1
    assert resp is not None


class _FakeObs:
    def __init__(self):
        self.updates: dict = {}

    def update(self, **kw):
        self.updates.update(kw)

    def end(self):
        pass


def test_finish_generation_reports_full_io_from_http_layer():
    """HTTP 层回填的完整请求/响应优先于 SDK 级摘要进入 generation。"""
    from book_agent import trace as trace_mod

    handle = trace_mod._Handle()
    handle.obs = _FakeObs()
    handle.cv_token = trace_mod._current_generation.set(handle)
    try:
        trace_mod.record_generation_request(request={"model": "m", "tools": [{"name": "t"}]})
        trace_mod.record_generation_response(response={"choices": [{"message": {"content": "全文"}}]})
        trace_mod.finish_generation(
            handle,
            output=[{"text": "摘要（应被覆盖）"}],
            usage={"prompt_tokens": 5, "completion_tokens": 2},
        )
    finally:
        # 正常路径 finish_generation 自己 reset；这里兜底防泄漏
        try:
            trace_mod._current_generation.set(None)
        except Exception:
            pass

    assert handle.obs.updates["input"] == {"model": "m", "tools": [{"name": "t"}]}
    assert handle.obs.updates["output"] == {"choices": [{"message": {"content": "全文"}}]}
    assert handle.obs.updates["usage_details"] == {"input": 5, "output": 2, "total": 7}
    assert trace_mod._current_generation.get() is None


def test_finish_generation_falls_back_without_full_io():
    """HTTP 层没回填时（如拦截器未触发），退回调用方传的摘要，input 不动。"""
    from book_agent import trace as trace_mod

    handle = trace_mod._Handle()
    handle.obs = _FakeObs()
    trace_mod.finish_generation(handle, output=[{"text": "fallback"}])

    assert handle.obs.updates["output"] == [{"text": "fallback"}]
    assert "input" not in handle.obs.updates
