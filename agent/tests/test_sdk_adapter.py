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
    assert len(ftools) == len(ALL_TOOLS) == 20
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
