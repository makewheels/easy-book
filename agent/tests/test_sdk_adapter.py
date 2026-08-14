"""Agents SDK 适配层测试（离线）：FunctionTool 包装与 BookTools.execute 的衔接。"""

from __future__ import annotations

import asyncio
import json

from book_agent.assistant import build_agent_tools
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
