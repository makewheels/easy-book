"""离线行为测试：写确认协议、未知工具、参数错误 —— 不需要后端和 LLM。"""

from __future__ import annotations

from book_agent.schema import ALL_TOOLS, WRITE_TOOLS
from book_agent.tools import BookTools, _weekday_of


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


def test_confirm_true_passes_gate():
    # 指向不可达端口：confirm=True 应越过门控真正发请求（得到连接错误返回值，而非 requiresConfirmation）
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    result = tools.execute("create_student", {"name": "测试", "confirm": True})
    assert "requiresConfirmation" not in result
    assert "error" in result


def test_planned_excludes_confirm_flag():
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    result = tools.execute("delete_student", {"student_id": "abc", "confirm": False})
    assert result["planned"] == {"student_id": "abc"}


def test_write_schemas_carry_confirm_param():
    for tool in ALL_TOOLS:
        fn = tool["function"]
        if fn["name"] in WRITE_TOOLS:
            props = fn["parameters"]["properties"]
            assert "confirm" in props, fn["name"]
            assert "confirm" not in fn["parameters"].get("required", []), fn["name"]


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


def test_weekday_of():
    assert _weekday_of("2026-08-19T21:00:00") == "周三"
    assert _weekday_of("2026-08-14") == "周五"
    assert _weekday_of("not-a-date") is None
    assert _weekday_of("") is None


def test_book_appointment_planned_includes_weekday():
    # 生产事故复现：模型曾把"下周三"算成 8/20（实为周四）；计划里带星期几供核对
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    result = tools.execute("book_appointment", {"student_id": "s1", "start_time": "2026-08-19T21:00:00"})
    assert result["requiresConfirmation"] is True
    assert result["planned"]["weekday"] == "周三"


def test_book_appointment_invalid_time_planned_still_works():
    tools = BookTools(api_url="http://localhost:1", confirm_write=False)
    result = tools.execute("book_appointment", {"student_id": "s1", "start_time": "乱七八糟"})
    assert result["requiresConfirmation"] is True
    assert "weekday" not in result["planned"]


def test_book_appointment_result_includes_weekday(monkeypatch):
    tools = BookTools(api_url="http://localhost:1", confirm_write=True)
    monkeypatch.setattr(tools, "_request", lambda *a, **k: {"id": "apt1", "status": "scheduled"})
    result = tools.execute(
        "book_appointment", {"student_id": "s1", "start_time": "2026-08-19T21:00:00", "confirm": True}
    )
    assert result["id"] == "apt1"
    assert result["weekday"] == "周三"
