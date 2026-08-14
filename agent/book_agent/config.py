"""Easy-Book agent 配置 — 从 agent/.env 自动加载环境变量。

环境变量前缀 BOOK_AGENT_*，LLM 默认走 DashScope 兼容模式（可改任意 OpenAI 兼容端点）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """从 agent/ 目录加载 .env（若存在）。"""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    with env_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if val and (val.startswith('"') or val.startswith("'")):
                val = val[1:-1]
            if key and val and key not in os.environ:
                os.environ[key] = val


_load_dotenv()

# ── 常见 provider 默认值 ──────────────────────────────────
_PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
}


@dataclass
class AgentConfig:
    """从环境变量解析的 agent 配置。"""

    # ── LLM ──
    provider: str = "dashscope"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: float = 120.0

    # ── easy-book 后端 ──
    easy_book_api_url: str = "http://localhost:8002"
    confirm_write: bool = False

    # ── 观测 ──
    # trace 环境标签（langfuse environment）；默认按后端地址推断
    environment: str = ""

    # ── paths ──
    project_root: str = field(default_factory=lambda: str(Path(__file__).resolve().parents[1]))

    def __post_init__(self) -> None:
        self._resolve()

    def _resolve(self) -> None:
        self.provider = (
            os.getenv("BOOK_AGENT_PROVIDER")
            or os.getenv("BOOK_AGENT_LLM_PROVIDER")
            or self.provider
        )

        self.api_key = (
            os.getenv("BOOK_AGENT_LLM_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )

        self.base_url = os.getenv("BOOK_AGENT_LLM_BASE_URL") or ""
        if not self.base_url:
            provider_defaults = _PROVIDER_DEFAULTS.get(self.provider, {})
            self.base_url = os.getenv("OPENAI_BASE_URL") or provider_defaults.get("base_url", "")

        self.model = os.getenv("BOOK_AGENT_LLM_MODEL") or ""
        if not self.model:
            provider_defaults = _PROVIDER_DEFAULTS.get(self.provider, {})
            self.model = os.getenv("OPENAI_MODEL") or provider_defaults.get("model", "")

        self.easy_book_api_url = os.getenv("EASY_BOOK_API_URL") or self.easy_book_api_url
        self.confirm_write = os.getenv("BOOK_AGENT_CONFIRM_WRITE", "").lower() in ("1", "true", "yes")
        self.environment = os.getenv("BOOK_AGENT_ENVIRONMENT") or (
            "development" if ("localhost" in self.easy_book_api_url or "127.0.0.1" in self.easy_book_api_url)
            else "production"
        )

        try:
            self.temperature = float(os.getenv("BOOK_AGENT_TEMPERATURE", str(self.temperature)))
        except ValueError:
            pass
        try:
            self.max_tokens = int(os.getenv("BOOK_AGENT_MAX_TOKENS", str(self.max_tokens)))
        except ValueError:
            pass
        try:
            self.timeout = float(os.getenv("BOOK_AGENT_TIMEOUT", str(self.timeout)))
        except ValueError:
            pass


_config: AgentConfig | None = None


def get_config() -> AgentConfig:
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config
