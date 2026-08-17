"""Chainlit Web UI：easy-book agent 的聊天界面（easybook.a4.fit/ai）。

启动（本地）：
  uv sync --extra web --extra langfuse
  uv run chainlit run chainlit_app.py --port 8003 --headless

生产由 deploy/agent.Dockerfile 构建，带 --root-path /ai 挂在 easybook.a4.fit/ai 下。
工具调用通过 tool_hook 实时渲染成可折叠 step（调用链展示）。

个性化能力（设计见 docs/agent-memory-and-suggestions.md）：
- 开场建议 starters：后端 /api/agent/suggestions 按系统状态动态生成
  （低余额续课/今日签到/本月营收…），后端不可达时退回静态兜底
- 用户身份：nginx auth_request 校验 eb_token 后透传 X-User-Id（手机号），
  WebSocket 握手头里可读（session.environ["HTTP_X_USER_ID"]）
- 用户记忆：会话开始注入该教练的记忆（extra_system）；对话中可用
  save_user_memory 工具记录；会话结束再用轻量 LLM 抽取一次
- 每轮提问记入 agent_queries（意图统计 → 建议个性化排序）
- 每条回答附 3 个个性化建议按钮（Action），点击 = 直接提问
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

import chainlit as cl
import requests
from openai import AsyncOpenAI

from book_agent.assistant import BookAssistant
from book_agent.config import get_config
from book_agent import trace as lf_trace

# 登录不在这里做：/ai 由前端 nginx 的 auth_request 统一拦截（未登录跳回
# easybook.a4.fit/login），登录态是写在 eb_token cookie 里的全站会话。
# Chainlit 自身保持无认证（仅集群内可达，入口只有 nginx）。

# 工具 → 意图映射：提问记录用，建议个性化排序的依据
INTENT_BY_TOOL = {
    "lessons_overview": "low_balance",
    "adjust_package_lessons": "low_balance",
    "profit_stats": "monthly_profit",
    "get_schedule": "today_checkin",
    "list_student_appointments": "today_checkin",
    "checkin_appointment": "today_checkin",
    "get_schedule_range": "tomorrow_schedule",
    "create_student": "new_student",
    "create_package": "no_package",
    "update_package": "no_package",
    "book_appointment": "book_appointment",
    "save_user_memory": "memory",
}

MEMORY_EXTRACT_PROMPT = """下面是一位游泳教练与课程管理助手的对话。请抽取值得长期记住的信息，
只保留以后还有用的（习惯偏好/业务规则/学员相关信息/未完成事项/时间规律），
一次性的事（某次约课、某个临时查询）不要。

输出 JSON 数组，每项 {"kind": ..., "content": ...}，kind 取值：
preference（偏好习惯）/ fact（业务事实）/ person（学员相关）/ process（未完成事项）/ pattern（时间规律）。
没有可记的就输出 []。只输出 JSON，不要解释。

对话：
{conversation}"""


def _api_url() -> str:
    return get_config().easy_book_api_url.rstrip("/")


def _service_headers() -> dict:
    key = get_config().service_key
    return {"X-Service-Key": key} if key else {}


def _get_user_id() -> str:
    """从 WebSocket 握手环境取用户身份（nginx 透传的 X-User-Id → HTTP_X_USER_ID）。"""
    try:
        environ = getattr(cl.context.session, "environ", None) or {}
        return environ.get("HTTP_X_USER_ID", "") or ""
    except Exception:  # noqa: BLE001 — 取不到身份不阻塞聊天
        return ""


def _log_query(user_id: str, text: str, tools: list[str]) -> None:
    """提问落库（习惯统计）；失败只记日志不阻塞。"""
    intent = next((INTENT_BY_TOOL[t] for t in tools if t in INTENT_BY_TOOL), "general")
    try:
        requests.post(f"{_api_url()}/api/agent/queries", json={
            "user_id": user_id, "text": text, "intent": intent, "tools": tools,
        }, headers=_service_headers(), timeout=3)
    except Exception:  # noqa: BLE001
        pass


def _fetch_memories(user_id: str) -> list[dict]:
    try:
        resp = requests.get(f"{_api_url()}/api/agent/memories",
                            params={"user_id": user_id}, headers=_service_headers(), timeout=3)
        return resp.json().get("data", {}).get("memories", [])
    except Exception:  # noqa: BLE001
        return []


def _memory_system_text(user_id: str) -> str:
    """该用户的记忆 → 系统提示词补充段落（空则不注入）。"""
    if not user_id:
        return ""
    memories = _fetch_memories(user_id)[:15]
    if not memories:
        return ""
    lines = "\n".join(f"- [{m['kind']}] {m['content']}" for m in memories)
    return (
        f"## 你对这位教练的记忆\n{lines}\n"
        "自然地运用这些记忆（称呼、默认参数、跟进未完成事项）；与实时查询结果冲突时以查询为准。"
    )


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


# ── 开场建议（动态）──────────────────────────────────────────

FALLBACK_STARTERS = [
    cl.Starter(label="学员课时总览", message="现在有哪些学员？各自的课时余额怎么样？"),
    cl.Starter(label="明天的课程", message="明天有什么课？"),
    cl.Starter(label="本月利润", message="这个月利润多少？"),
]


@cl.set_starters
async def _starters(user=None, language=None) -> list[cl.Starter]:
    """状态驱动的开场建议：续课提醒/今日签到/本月营收等。

    注意：此回调拿不到会话上下文（页面加载时调用），个性化排序在
    对话内的建议按钮（Action）里做——那里有用户身份。
    """
    def fetch():
        resp = requests.get(f"{_api_url()}/api/agent/suggestions",
                            params={"limit": 4}, headers=_service_headers(), timeout=5)
        return resp.json().get("data", {}).get("suggestions", [])

    try:
        items = await asyncio.to_thread(fetch)
        if items:
            return [cl.Starter(label=s["label"], message=s["message"]) for s in items]
    except Exception:  # noqa: BLE001 — 后端不可达退回静态建议
        pass
    return FALLBACK_STARTERS


# ── 会话生命周期 ─────────────────────────────────────────────


@cl.on_chat_start
async def on_chat_start() -> None:
    cfg = get_config()
    user_id = _get_user_id()
    cl.user_session.set("user_id", user_id)
    memory_text = await asyncio.to_thread(_memory_system_text, user_id)
    assistant = BookAssistant(
        tools=None,
        tool_hook=_tool_hook,
        extra_system=memory_text,
    )
    # 用户身份传给工具层：save_user_memory 按人归属
    assistant.tools.user_id = user_id
    cl.user_session.set("assistant", assistant)
    # 注意：不发开场问候——Chainlit 的 starters 只在空会话时展示，
    # 发了消息建议按钮就被隐藏。开场引导交给 starters 承担。


async def _handle_user_text(text: str) -> None:
    """一轮对话：执行 → 回答 → 提问落库 → 附个性化建议按钮。"""
    assistant: BookAssistant = cl.user_session.get("assistant")
    user_id: str = cl.user_session.get("user_id", "")
    session_id = cl.context.session.id

    msg = cl.Message(content="")
    await msg.send()

    tools_used: list[str] = []
    try:
        result = await assistant.answer_async(
            text, session_id=session_id, use_history=True
        )
        msg.content = result["answer"] or "（没有返回内容）"
        tools_used = [
            e["tool"] for e in result["trace"]
            if not (isinstance(e.get("result"), dict) and e["result"].get("requiresConfirmation"))
        ]
    except Exception as exc:  # noqa: BLE001 — UI 层兜底，给出可读错误
        msg.content = f"⚠️ 出错了：{exc}"
    finally:
        lf_trace.flush()

    # 个性化建议按钮（有身份才个性化；拉取失败不挂按钮）
    actions: list[cl.Action] = []
    try:
        resp = await asyncio.to_thread(
            requests.get, f"{_api_url()}/api/agent/suggestions",
            params={"user_id": user_id, "limit": 3}, headers=_service_headers(), timeout=3,
        )
        for s in resp.json().get("data", {}).get("suggestions", []):
            actions.append(cl.Action(
                name="suggest_question", label=s["label"],
                payload={"message": s["message"]},
            ))
    except Exception:  # noqa: BLE001
        pass
    if actions:
        msg.actions = actions
    await msg.update()

    if text:
        await asyncio.to_thread(_log_query, user_id, text, tools_used)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    await _handle_user_text(message.content)


@cl.action_callback("suggest_question")
async def on_suggest_question(action: cl.Action) -> None:
    """点击建议按钮 = 用户提出该问题。先展示成用户消息再走正常对话。"""
    message = (action.payload or {}).get("message", "")
    if not message:
        return
    await cl.Message(content=message, author="用户").send()
    await _handle_user_text(message)


@cl.on_chat_end
async def on_chat_end() -> None:  # noqa: C901
    """会话结束：用轻量调用从对话里抽取长期记忆（习惯/规则/学员信息/未完成事项）。"""
    assistant: BookAssistant | None = cl.user_session.get("assistant")
    user_id: str = cl.user_session.get("user_id", "")
    if assistant is None or not assistant.history:
        return
    # 只保留 user/assistant 文本轮，截断防超长
    turns: list[str] = []
    for item in assistant.history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            turns.append(f"{'教练' if role == 'user' else '助手'}: {content[:500]}")
    if len(turns) < 2:
        return
    conversation = "\n".join(turns[-30:])

    cfg = get_config()
    if not cfg.api_key:
        return
    try:
        client = AsyncOpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=30)
        resp = await client.chat.completions.create(
            model=cfg.model,
            messages=[{"role": "user",
                       "content": MEMORY_EXTRACT_PROMPT.format(conversation=conversation)}],
            max_tokens=500,
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        items = json.loads(raw) if raw else []
    except Exception:  # noqa: BLE001 — 抽取失败不影响用户体验
        return

    for item in items[:5]:  # 每次会话最多入库 5 条，防刷
        if not isinstance(item, dict) or not item.get("content"):
            continue
        try:
            requests.post(f"{_api_url()}/api/agent/memories", json={
                "user_id": user_id,
                "kind": item.get("kind", "fact"),
                "content": str(item["content"])[:500],
                "source": "llm_extract",
                "confidence": 0.6,
            }, headers=_service_headers(), timeout=3)
        except Exception:  # noqa: BLE001
            pass
