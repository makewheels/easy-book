"""book-agent 命令行入口。

用法：
  book-agent ask "明天有什么课"          # 单轮问答
  book-agent chat                        # 交互式多轮对话
  book-agent tools                       # 打印全部工具 schema（JSON）
  book-agent health                      # 检查后端连通性

公共参数：
  --api-url http://localhost:8002       # easy-book 后端地址
  --confirm-write                       # 跳过写确认直接执行（慎用）
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from .assistant import BookAssistant
from .client import LLMError
from .config import get_config
from .schema import ALL_TOOLS
from .tools import BookTools
from . import trace as lf_trace


def _api_url(args: argparse.Namespace) -> str:
    # 未显式传 --api-url 时取配置（agent/.env 的 EASY_BOOK_API_URL）
    return args.api_url or get_config().easy_book_api_url


def _build_assistant(args: argparse.Namespace) -> BookAssistant:
    tools = BookTools(api_url=_api_url(args), confirm_write=args.confirm_write)
    return BookAssistant(tools=tools)


def _print_trace(trace: list) -> None:
    if not trace:
        return
    print("\n── 工具调用 ──", file=sys.stderr)
    for i, t in enumerate(trace, 1):
        args_str = json.dumps(t["args"], ensure_ascii=False)
        print(f"  {i}. {t['tool']}({args_str})  [{t['elapsed_seconds']}s]", file=sys.stderr)


def cmd_ask(args: argparse.Namespace) -> int:
    assistant = _build_assistant(args)
    try:
        result = assistant.answer(args.query)
    except LLMError as exc:
        print(f"LLM 错误: {exc}", file=sys.stderr)
        return 2
    print(result["answer"])
    _print_trace(result["trace"])
    lf_trace.flush()
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    assistant = _build_assistant(args)
    history: list = []
    session_id = f"chat-{uuid.uuid4().hex[:8]}"
    print("Easy-Book 助手（输入 quit 退出）")
    while True:
        try:
            query = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            lf_trace.flush()
            return 0
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            lf_trace.flush()
            return 0
        try:
            result = assistant.answer(query, history=history, session_id=session_id)
        except LLMError as exc:
            print(f"LLM 错误: {exc}", file=sys.stderr)
            continue
        print(f"助手 > {result['answer']}")
        _print_trace(result["trace"])
        # 保留本轮对话（去掉 system，下轮重建以刷新日期）
        history = [m for m in result["messages"] if m["role"] != "system"]


def cmd_tools(args: argparse.Namespace) -> int:
    print(json.dumps(ALL_TOOLS, ensure_ascii=False, indent=2))
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    api_url = _api_url(args)
    tools = BookTools(api_url=api_url)
    try:
        result = tools._request("GET", "/health")
        print(f"后端正常 ({api_url}): {result}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"后端不可达 ({api_url}): {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="book-agent", description="Easy-Book 自然语言助手")
    parser.add_argument("--api-url", default=None, help="easy-book 后端地址（默认取 EASY_BOOK_API_URL 配置）")
    parser.add_argument("--confirm-write", action="store_true", help="写操作免确认直接执行（慎用）")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask", help="单轮问答")
    p_ask.add_argument("query", help="问题，如：明天有什么课")

    sub.add_parser("chat", help="交互式多轮对话")
    sub.add_parser("tools", help="打印工具 schema")
    sub.add_parser("health", help="检查后端连通性")

    args = parser.parse_args(argv)
    handlers = {"ask": cmd_ask, "chat": cmd_chat, "tools": cmd_tools, "health": cmd_health}
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
