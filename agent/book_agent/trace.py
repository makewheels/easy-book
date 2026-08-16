"""Langfuse trace 观测层（可选依赖，未配置时整体 no-op）。

模式同 video-2022 ai-agent/video_agent/trace.py：
- 不配 `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_HOST` 时整体 no-op，本地/测试零侵入
- 任何异常只记 warning 不抛——绝不让 trace 拖垮主路径
- langfuse 是可选依赖（`uv sync --extra langfuse`），SDK 后台线程批量上报

埋点：
- `BookAssistant.answer` → 每次问答一个 trace（根 span）
- `_TracedModel.get_response`（assistant.py，包 Agents SDK 模型）→ generation（model / messages / usage / 延迟）
- `BookTools.execute` → tool span

generation 的 input/output 会被 HTTP 层拦截器（assistant.py 包装 `chat.completions.create`）
回填为**发给 LLM 的完整原始请求体**（含 messages/tools/全部生成参数）与**完整原始响应体**，
即 Langfuse 里看到的 generation input/output 就是线上真实收发的原文，一字不少。

trace 结构：一次问答 = 一个 trace，期间产生的 generation 和 tool span 通过
contextvars 自动挂到它下面；`session_id` / `environment` 是 trace 级属性，
经 `propagate_attributes` 下发。
"""

from __future__ import annotations

import logging
import os
import time
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

_client: Any = None
_tried_init = False


def _get_client() -> Any | None:
    """懒加载单例。未配置 env 或 SDK 初始化失败都返回 None（= 关闭）。

    dev/prod 双 project：environment=production 且配置了 LANGFUSE_PROD_* 时
    用生产 project 的 key（easy-book-prod），否则用默认 key（easy-book-dev）。
    """
    global _client, _tried_init
    if _tried_init:
        return _client
    _tried_init = True
    if not os.environ.get("LANGFUSE_SECRET_KEY"):
        return None
    try:
        from langfuse import Langfuse

        from .config import get_config

        if get_config().environment == "production" and os.environ.get("LANGFUSE_PROD_SECRET_KEY"):
            _client = Langfuse(
                public_key=os.environ["LANGFUSE_PROD_PUBLIC_KEY"],
                secret_key=os.environ["LANGFUSE_PROD_SECRET_KEY"],
                host=os.environ.get("LANGFUSE_HOST"),
            )
        else:
            _client = Langfuse()  # 读 LANGFUSE_SECRET_KEY / LANGFUSE_PUBLIC_KEY / LANGFUSE_HOST
        logger.info(
            "langfuse trace 已启用 → %s（%s key）",
            os.environ.get("LANGFUSE_HOST", "(cloud)"),
            "prod" if os.environ.get("LANGFUSE_PROD_SECRET_KEY") and get_config().environment == "production" else "dev",
        )
    except Exception as e:
        logger.warning("langfuse 初始化失败，trace 关闭（不影响主路径）: %s", e)
        _client = None
    return _client


# 当前活跃的 generation 句柄：供 HTTP 层拦截器（assistant.py 的 create 包装）
# 在不经过 SDK 参数链的情况下找到正在上报的 generation，回填完整原始请求/响应。
_current_generation: ContextVar["_Handle | None"] = ContextVar(
    "lf_current_generation", default=None
)


class _Handle:
    """一次观测的句柄：已 enter 的 context manager 列表 + 观测对象 + 起始时间。

    未启用 langfuse 时所有 start_* 返回 None，对应的 finish/end 收到 None 直接 no-op。
    """

    __slots__ = ("cms", "obs", "t0", "trace_id", "cv_token", "full_input", "full_output")

    def __init__(self) -> None:
        self.cms: list[Any] = []
        self.obs: Any = None
        self.t0: float = time.monotonic()
        self.trace_id: str | None = None
        self.cv_token: Any = None
        # HTTP 层记录的完整原始请求/响应；finish 时优先于 SDK 级摘要上报
        self.full_input: Any = None
        self.full_output: Any = None


def _close(handle: _Handle) -> None:
    """按相反顺序退出所有已 enter 的 context manager（幂等）。"""
    while handle.cms:
        cm = handle.cms.pop()
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


def _latency_ms(handle: _Handle) -> int:
    return int((time.monotonic() - handle.t0) * 1000)


def _usage_details(usage: dict | None) -> dict | None:
    """OpenAI 风格 usage → langfuse usage_details。"""
    if not usage:
        return None
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    total = int(usage.get("total_tokens") or (prompt + completion))
    if not (prompt or completion or total):
        return None
    return {"input": prompt, "output": completion, "total": total}


# ── generation（LLM 调用） ─────────────────────────────────────


def start_generation(
    *,
    name: str = "model.chat",
    model: str | None = None,
    messages: Any = None,
    metadata: dict | None = None,
) -> _Handle | None:
    """LLM 调用前开始一个 generation。未启用返回 None。"""
    client = _get_client()
    if client is None:
        return None
    handle = _Handle()
    try:
        handle.obs = client.start_observation(
            name=name,
            as_type="generation",
            model=model,
            input=messages,
            metadata=metadata,
        )
        handle.cv_token = _current_generation.set(handle)
        return handle
    except Exception as e:
        logger.warning("langfuse start_generation 失败（不影响主路径）: %s", e)
        return None


def record_generation_request(*, request: Any) -> None:
    """HTTP 层拦截器回填：发给 LLM 的完整原始请求体。无活跃 generation 时 no-op。"""
    handle = _current_generation.get()
    if handle is not None:
        handle.full_input = request


def record_generation_response(*, response: Any) -> None:
    """HTTP 层拦截器回填：LLM 返回的完整原始响应体。无活跃 generation 时 no-op。"""
    handle = _current_generation.get()
    if handle is not None:
        handle.full_output = response


def finish_generation(
    handle: _Handle | None,
    *,
    output: Any = None,
    usage: dict | None = None,
    error: BaseException | str | None = None,
) -> None:
    """结束 generation 并回填 output/usage/延迟。handle 为 None（未启用）时什么都不做。"""
    if handle is None:
        return
    try:
        if handle.obs is not None:
            update_kw: dict[str, Any] = {
                # HTTP 层记录的完整响应优先；没有才退回调用方传的摘要
                "output": handle.full_output if handle.full_output is not None else output,
                "usage_details": _usage_details(usage),
                "level": "ERROR" if error else "DEFAULT",
                "status_message": str(error) if error else None,
                "metadata": {"latencyMs": _latency_ms(handle)},
            }
            # HTTP 层记录的完整请求（含 tools/参数）覆盖 start 时的 messages 快照
            if handle.full_input is not None:
                update_kw["input"] = handle.full_input
            handle.obs.update(**update_kw)
            handle.obs.end()
    except Exception as e:
        logger.warning("langfuse finish_generation 失败（不影响主路径）: %s", e)
    finally:
        _close(handle)
        if handle.cv_token is not None:
            try:
                _current_generation.reset(handle.cv_token)
            except (LookupError, ValueError):
                pass


# ── tool span（工具执行） ──────────────────────────────────────


def start_tool_span(name: str, args: dict | None = None) -> _Handle | None:
    """工具执行前开始一个 tool span。未启用返回 None。"""
    client = _get_client()
    if client is None:
        return None
    handle = _Handle()
    try:
        handle.obs = client.start_observation(name=f"tool:{name}", as_type="tool", input=args)
        return handle
    except Exception as e:
        logger.warning("langfuse start_tool_span 失败（不影响主路径）: %s", e)
        return None


def finish_tool_span(
    handle: _Handle | None,
    *,
    result: Any = None,
    error: BaseException | str | None = None,
) -> None:
    """结束 tool span。result 是带 "error" 键的 dict 也视为失败。"""
    if handle is None:
        return
    failed = error is not None or (isinstance(result, dict) and "error" in result)
    try:
        if handle.obs is not None:
            handle.obs.update(
                output=result,
                level="ERROR" if failed else "DEFAULT",
                status_message=(str(error) if error else (result.get("error") if failed else None)),
                metadata={"latencyMs": _latency_ms(handle)},
            )
            handle.obs.end()
    except Exception as e:
        logger.warning("langfuse finish_tool_span 失败（不影响主路径）: %s", e)
    finally:
        _close(handle)


# ── trace（一次问答） ─────────────────────────────────────────


def start_trace(
    *,
    name: str,
    input: Any = None,
    session_id: str | None = None,
    user_id: str | None = None,
    environment: str | None = None,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> _Handle | None:
    """开始一个 trace 并设为当前上下文——期间产生的 generation/tool span 都挂在它下面。

    返回的句柄带 trace_id；未启用返回 None。
    """
    client = _get_client()
    if client is None:
        return None
    handle = _Handle()
    try:
        from langfuse import propagate_attributes

        kw: dict[str, Any] = {"trace_name": name}
        if session_id:
            kw["session_id"] = session_id
        if user_id:
            kw["user_id"] = user_id
        if environment:
            kw["environment"] = environment
        if tags:
            kw["tags"] = tags
        cm = propagate_attributes(**kw)
        cm.__enter__()
        handle.cms.append(cm)

        span_cm = client.start_as_current_observation(
            name=name, as_type="span", input=input, metadata=metadata
        )
        handle.obs = span_cm.__enter__()
        handle.cms.append(span_cm)
        handle.trace_id = client.get_current_trace_id()
        return handle
    except Exception as e:
        logger.warning("langfuse start_trace 失败（不影响主路径）: %s", e)
        _close(handle)
        return None


def end_trace(
    handle: _Handle | None,
    *,
    output: Any = None,
    error: BaseException | str | None = None,
) -> None:
    """结束 trace 根 span（退出上下文；span_cm 退出时自动 end）。"""
    if handle is None:
        return
    try:
        if handle.obs is not None:
            handle.obs.update(
                output=output,
                level="ERROR" if error else "DEFAULT",
                status_message=str(error) if error else None,
                metadata={"latencyMs": _latency_ms(handle)},
            )
    except Exception as e:
        logger.warning("langfuse end_trace 失败（不影响主路径）: %s", e)
    finally:
        _close(handle)


def flush() -> None:
    """短生命周期进程（ask CLI）退出前冲一次队列；SDK 后台线程也会定时 flush。"""
    client = _get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as e:
        logger.warning("langfuse flush 失败: %s", e)
