"""离线行为测试：写确认协议、未知工具、参数错误 —— 不需要后端和 LLM。"""

from __future__ import annotations

from book_agent.schema import ALL_TOOLS, WRITE_TOOLS
from book_agent.tools import BookTools


def test_write_requires_confirmation_by_default():
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    result = tools.execute("create_student", {"name": "测试"})
    assert result["requiresConfirmation"] is True
    assert result["tool"] == "create_student"
    assert result["planned"] == {"name": "测试"}
    # 未确认时不应产生真实调用（trace 记录了拦截）
    assert tools.trace[-1]["result"]["requiresConfirmation"] is True


def test_all_write_tools_gated():
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    for name in WRITE_TOOLS:
        result = tools.execute(name, {})
        assert isinstance(result, dict) and result.get("requiresConfirmation") is True, name


def test_unknown_tool_returns_error():
    tools = BookTools()
    result = tools.execute("fly_to_moon", {})
    assert "error" in result


def test_private_name_not_dispatchable():
    tools = BookTools()
    result = tools.execute("_request", {"method": "GET", "path": "/"})
    assert "error" in result


def test_type_error_converted_to_value():
    tools = BookTools(confirm_write=True)
    # adjust_package_lessons 要求 delta，缺失时 TypeError → 错误返回值
    result = tools.execute("adjust_package_lessons", {"package_id": "x"})
    assert "error" in result


def test_tools_count_and_names_stable():
    names = {t["function"]["name"] for t in ALL_TOOLS}
    # 20 个工具：9 查询 + 11 写操作
    assert len(names) == 20
    assert len(WRITE_TOOLS) == 11
