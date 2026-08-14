"""Agent — 基于 OpenAI Agents SDK 的 tool-use agent（2026-08-14 由手写 loop 迁移）。

架构约定不变：
- 工具执行层仍是 BookTools（方法名即工具名、写确认协议、错误转返回值）
- ALL_TOOLS schema 通过适配层转成 SDK FunctionTool（契约测试继续钉 schema↔方法对齐）
- Langfuse 埋点：answer → trace 根 span；LLM 调用经 _TracedModel 包一层 generation span；
  工具 span 在 BookTools.execute 里。SDK 自带 tracing 已关闭（不上报 OpenAI）。
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from agents import Agent, FunctionTool, Model, ModelSettings, Runner, set_tracing_disabled
from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from .config import get_config
from .schema import ALL_TOOLS
from .tools import BookTools
from . import trace as lf_trace

# 关闭 SDK 自带 tracing（默认会尝试上报 OpenAI）；观测统一走 Langfuse
set_tracing_disabled(True)


class LLMError(RuntimeError):
    pass


def build_system_prompt(now: datetime | None = None) -> str:
    """生成系统提示词；注入当前日期，模型才能正确换算“明天/下周一”。"""
    now = now or datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today = f"{now.strftime('%Y-%m-%d')}（{weekdays[now.weekday()]}）"

    return f"""你是 Easy-Book 泳课学员管理系统的 AI 助手，帮游泳教练管理学员、课包、约课、签到和财务。

今天是 {today}。涉及“今天/明天/下周”等相对日期时，先换算成 YYYY-MM-DD 绝对日期再调工具。

## 核心规则

1. **写操作必须确认**：新增/修改/删除/签到/扣课时等改数据的操作，工具会返回 requiresConfirmation。
   此时你要把计划（做什么、涉及谁、关键数字）清楚告诉用户并等待确认，用户同意后才带 confirm=true 再次调用同一工具执行。
   未确认前不得猜测执行结果。
2. **先查再改**：用户用姓名指代学员时，先 search_students 拿 student_id；
   改套餐先 list_student_packages 拿 package_id；改预约先 get_schedule / list_student_appointments 拿 appointment_id。
   绝不编造 id。
3. **有歧义就追问**：搜索返回多个同名学员时，列出候选让用户选，不要猜。
4. **数据准确**：课时数、金额、时间必须来自工具返回，不要编造；金额保留两位小数。
5. **中文回答**：简洁、口语化，关键数字清晰列出。

## 工具选择指南

- 明天/某天有什么课 → get_schedule(date)
- 这周/一段时间的课 → get_schedule_range
- 学员还有多少课时 → search_students（含 remaining_lessons）或 lessons_overview（全员+低余额预警）
- 学员的课包明细 → list_student_packages
- 利润/营收/分成统计 → profit_stats（可带月份范围）
- 新增学员 → create_student；改资料 → update_student
- 买课包/续费 → create_package（记次给 total_lessons，时长给起止日期）
- 加次数/扣次数 → adjust_package_lessons（delta 正加负扣）
- 设置财务分成 → update_package 改 venue_share（上交俱乐部金额，利润=price-venue_share）
- 约课 → book_appointment（start_time 用 ISO 格式本地时间）
- 取消约课 → cancel_appointment；标记旷课 → set_appointment_status(no_show)
- 签到（扣课时）→ checkin_appointment"""


def build_agent_tools(
    book_tools: BookTools,
    tool_hook: Any = None,
) -> list[FunctionTool]:
    """ALL_TOOLS schema → SDK FunctionTool；执行统一走 BookTools.execute（保留写确认/错误转返回值）。

    tool_hook：可选异步钩子 `async hook(name, args, run) -> result`（run 为执行函数），
    供 UI 层（如 Chainlit）在工具执行前后渲染调用链；不传则直接执行。
    """

    def _make(name: str):
        async def on_invoke(_ctx: Any, args_json: str) -> str:
            try:
                args = json.loads(args_json) if args_json else {}
            except json.JSONDecodeError:
                args = {"_raw_arguments": args_json}
            if tool_hook is not None:
                result = await tool_hook(name, args, lambda: book_tools.execute(name, args))
            else:
                result = book_tools.execute(name, args)
            return json.dumps(result, ensure_ascii=False, default=str)

        return on_invoke

    tools: list[FunctionTool] = []
    for t in ALL_TOOLS:
        fn = t["function"]
        tools.append(
            FunctionTool(
                name=fn["name"],
                description=fn["description"],
                params_json_schema=fn["parameters"],
                on_invoke_tool=_make(fn["name"]),
                # DashScope 兼容端点不支持 OpenAI strict 模式
                strict_json_schema=False,
            )
        )
    return tools


def _usage_from_sdk(usage: Any) -> dict | None:
    if usage is None:
        return None
    prompt = int(getattr(usage, "input_tokens", 0) or 0)
    completion = int(getattr(usage, "output_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", 0) or (prompt + completion))
    if not (prompt or completion or total):
        return None
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": total}


def _summarize_output(output: Any) -> Any:
    """ModelResponse.output → 精简可序列化的摘要（避免把整个响应塞进 trace）。"""
    if not output:
        return None
    summary: list[dict[str, Any]] = []
    for item in output:
        kind = getattr(item, "type", None)
        if kind == "function_call":
            summary.append({
                "tool_call": getattr(item, "name", ""),
                "arguments": getattr(item, "arguments", ""),
            })
        elif kind == "message":
            content = getattr(item, "content", None) or []
            text = "".join(getattr(c, "text", "") or "" for c in content)
            if text:
                summary.append({"text": text[:1000]})
    return summary or None


class _TracedModel(Model):
    """包装 OpenAIChatCompletionsModel：给每次 LLM 调用补 Langfuse generation span。"""

    def __init__(self, inner: OpenAIChatCompletionsModel, model_name: str) -> None:
        self._inner = inner
        self._model_name = model_name

    async def get_response(self, *args: Any, **kwargs: Any) -> Any:
        messages = args[1] if len(args) > 1 else kwargs.get("input")
        gen = lf_trace.start_generation(name="model.chat", model=self._model_name, messages=messages)
        try:
            resp = await self._inner.get_response(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — 记完 trace 原样抛给 SDK
            lf_trace.finish_generation(gen, error=exc)
            raise
        lf_trace.finish_generation(
            gen,
            output=_summarize_output(getattr(resp, "output", None)),
            usage=_usage_from_sdk(getattr(resp, "usage", None)),
        )
        return resp

    async def stream_response(self, *args: Any, **kwargs: Any) -> Any:
        # CLI 不用流式；真走到这里时逐事件透传（generation span 不覆盖流式）
        async for event in self._inner.stream_response(*args, **kwargs):
            yield event


class BookAssistant:
    """easy-book 助手：OpenAI Agents SDK 驱动，工具执行层为 BookTools。"""

    MAX_TURNS = 8

    def __init__(self, tools: BookTools | None = None, tool_hook: Any = None) -> None:
        cfg = get_config()
        self.tools = tools or BookTools(api_url=cfg.easy_book_api_url, service_key=cfg.service_key)
        self.tool_hook = tool_hook
        # SDK input items 历史（chat 多轮用；ask 单轮不用）
        self.history: list[Any] = []

    def _build_agent(self) -> Agent:
        cfg = get_config()
        if not cfg.api_key:
            raise LLMError(
                "未配置 LLM API key：请设置环境变量 BOOK_AGENT_LLM_API_KEY（或 DASHSCOPE_API_KEY），"
                "也可在 agent/.env 中配置"
            )
        if not cfg.base_url:
            raise LLMError("未配置 LLM base_url：请设置 BOOK_AGENT_LLM_BASE_URL")
        client = AsyncOpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=cfg.timeout)
        model = _TracedModel(OpenAIChatCompletionsModel(model=cfg.model, openai_client=client), cfg.model)
        return Agent(
            name="easy-book-assistant",
            instructions=build_system_prompt(),
            model=model,
            model_settings=ModelSettings(temperature=cfg.temperature, max_tokens=cfg.max_tokens),
            tools=build_agent_tools(self.tools, self.tool_hook),
        )

    async def answer_async(
        self, query: str, session_id: str | None = None, use_history: bool = False
    ) -> dict[str, Any]:
        """异步版：单轮（ask）或多轮（chat, use_history=True）问答，返回 {query, answer, trace}。"""
        cfg = get_config()
        self.tools.trace.clear()
        trace_handle = lf_trace.start_trace(
            name="book-agent.answer",
            input=query,
            session_id=session_id,
            environment=cfg.environment,
            metadata={
                "backend": self.tools.api_url,
                "framework": "openai-agents",
                "max_turns": self.MAX_TURNS,
            },
        )
        agent = self._build_agent()
        input_items: list[Any] = list(self.history) if use_history else []
        input_items.append({"role": "user", "content": query})

        try:
            result = await Runner.run(
                agent,
                input=input_items,
                max_turns=self.MAX_TURNS,
            )
        except Exception as exc:
            lf_trace.end_trace(trace_handle, error=exc)
            raise LLMError(str(exc)) from exc

        final_text = str(result.final_output or "")
        if use_history:
            self.history = list(result.to_input_list())
        lf_trace.end_trace(trace_handle, output=final_text)

        return {
            "query": query,
            "answer": final_text,
            "trace": list(self.tools.trace),
        }

    def answer(self, query: str, session_id: str | None = None, use_history: bool = False) -> dict[str, Any]:
        """同步入口（CLI 用）：包一层事件循环调 answer_async。"""
        return asyncio.run(self.answer_async(query, session_id=session_id, use_history=use_history))
