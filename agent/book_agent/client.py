"""OpenAI 兼容接口的最小 LLM 客户端（urllib 实现，零额外依赖）。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import AgentConfig, get_config
from .schema import ALL_TOOLS


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AgentResponse:
    text: str
    tool_calls: list[ToolCall]
    raw: dict[str, Any]


class LLMError(RuntimeError):
    pass


class ModelClient:
    """调用任意 OpenAI 兼容 /chat/completions 端点（DashScope/DeepSeek/OpenAI...）。"""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        cfg = config or get_config()
        self.model = model or cfg.model
        self.base_url = (base_url or cfg.base_url).rstrip("/")
        self.api_key = api_key or cfg.api_key
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens
        self.timeout = cfg.timeout

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> AgentResponse:
        """单轮非流式调用，返回文本与工具调用。"""
        if not self.api_key:
            raise LLMError(
                "未配置 LLM API key：请设置环境变量 BOOK_AGENT_LLM_API_KEY（或 DASHSCOPE_API_KEY），"
                "也可在 agent/.env 中配置"
            )
        if not self.base_url:
            raise LLMError("未配置 LLM base_url：请设置 BOOK_AGENT_LLM_BASE_URL")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"LLM HTTP {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"LLM 网络错误: {exc.reason}") from exc

        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"LLM 响应格式异常: {str(body)[:500]}") from exc

        text = message.get("content") or ""
        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function") or {}
            raw_args = fn.get("arguments") or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {"_raw_arguments": raw_args}
            tool_calls.append(ToolCall(id=tc.get("id") or "", name=fn.get("name") or "", arguments=args))

        return AgentResponse(text=text, tool_calls=tool_calls, raw=body)
