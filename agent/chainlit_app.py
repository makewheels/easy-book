"""Chainlit Web UI：easy-book agent 的聊天界面（easybook.a4.fit/ai）。

启动（本地）：
  uv sync --extra web --extra langfuse
  uv run chainlit run chainlit_app.py --port 8003 --headless

生产由 deploy/agent.Dockerfile 构建，带 --root-path /ai 挂在 easybook.a4.fit/ai 下。
工具调用通过 tool_hook 实时渲染成可折叠 step（调用链展示）。
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import chainlit as cl

from book_agent.assistant import BookAssistant
from book_agent import trace as lf_trace

# 登录不在这里做：/ai 由前端 nginx 的 auth_request 统一拦截（未登录跳回
# easybook.a4.fit/login），登录态是写在 eb_token cookie 里的全站会话。
# Chainlit 自身保持无认证（仅集群内可达，入口只有 nginx）。


async def _tool_hook(
    name: str,
    args: dict,
    run: Callable[[], Any],
) -> Any:
    """工具执行钩子：把每次工具调用渲染成一个 Chainlit step（入参/出参/耗时）。"""
    async with cl.Step(name=f"tool:{name}", type="tool") as step:
        step.input = args
        # execute 是同步的（requests），丢线程池避免阻塞事件循环
        result = await asyncio.to_thread(run)
        step.output = result
    return result


@cl.set_starters
async def _starters() -> list[cl.Starter]:
    return [
        cl.Starter(label="学员课时总览", message="现在有哪些学员？各自的课时余额怎么样？"),
        cl.Starter(label="明天的课程", message="明天有什么课？"),
        cl.Starter(label="本月利润", message="这个月利润多少？"),
        cl.Starter(label="新增学员", message="帮我新增一个学员"),
    ]


@cl.on_chat_start
async def on_chat_start() -> None:
    assistant = BookAssistant(tool_hook=_tool_hook)
    cl.user_session.set("assistant", assistant)
    await cl.Message(
        content=(
            "你好！我是泳课管理 AI 助手 👋\n\n"
            "我可以直接帮你：查课表、查学员课时、新增学员、买课包、约课、签到、算利润。\n"
            "涉及改数据的操作，我会先列出计划，等你确认后才执行。"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    assistant: BookAssistant = cl.user_session.get("assistant")
    session_id = cl.context.session.id

    # 先发占位消息：期间产生的工具 step 会挂在它下面，最后回填答案
    msg = cl.Message(content="")
    await msg.send()

    try:
        result = await assistant.answer_async(
            message.content, session_id=session_id, use_history=True
        )
        msg.content = result["answer"] or "（没有返回内容）"
    except Exception as exc:  # noqa: BLE001 — UI 层兜底，给出可读错误
        msg.content = f"⚠️ 出错了：{exc}"
    finally:
        lf_trace.flush()
    await msg.update()
