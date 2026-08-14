"""Live 测试：工具层直连本机 easy-book 后端跑通全流程。

后端（http://localhost:8002）不在线时整个文件 skip —— 与 CI/无后端环境兼容。
"""

from __future__ import annotations

import uuid

import pytest
import requests

from book_agent.tools import BookTools

API_URL = "http://localhost:8002"


def _backend_alive() -> bool:
    try:
        return requests.get(f"{API_URL}/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _backend_alive(), reason="easy-book 后端不在线（localhost:8002）")


@pytest.fixture
def tools():
    return BookTools(api_url=API_URL, confirm_write=True)


@pytest.fixture
def scratch_student(tools):
    """临时学员，测试结束级联删除。"""
    suffix = uuid.uuid4().hex[:8]
    student = tools.create_student(name=f"契约测试_{suffix}", phone="13900000000")
    yield student
    tools.delete_student(student["id"])


def test_student_package_appointment_checkin_flow(tools, scratch_student):
    sid = scratch_student["id"]

    # 搜索能找到
    found = tools.search_students(search=scratch_student["name"])
    assert any(s["id"] == sid for s in found)

    # 创建记次套餐
    pkg = tools.create_package(
        student_id=sid, name="测试包", package_type="1v1",
        price=1000.0, venue_share=200.0, total_lessons=5,
    )
    assert pkg["count_based_info"]["remaining_lessons"] == 5

    # 加次数
    adjusted = tools.adjust_package_lessons(package_id=pkg["id"], delta=3, adjust_total=True, reason="live测试")
    assert adjusted["lessons_after"] == 8

    # 学员聚合课时
    student = tools.get_student(sid)
    assert student["remaining_lessons"] == 8

    # 预约（用一个不太可能冲突的清晨时间）
    booked = tools.book_appointment(student_id=sid, start_time="2099-01-02T06:00:00", duration_minutes=60)
    apt_id = booked["id"]

    # 日程能查到
    schedule = tools.get_schedule("2099-01-02")
    assert any(s["appointment_id"] == apt_id for slot in schedule["slots"] for s in slot["students"])

    # 签到扣课时
    checkin = tools.checkin_appointment(appointment_id=apt_id, student_id=sid)
    assert checkin["lessons_after"] == 7

    # 重复签到：错误转返回值（execute 约定），不抛异常
    dup = tools.execute("checkin_appointment", {"appointment_id": apt_id, "student_id": sid})
    assert "error" in dup

    # 课时概览包含该学员
    overview = tools.lessons_overview()
    assert any(s["student_id"] == sid for s in overview["students"])


def test_profit_stats_shape(tools):
    stats = tools.profit_stats()
    for key in ("package_count", "total_revenue", "total_venue_share", "total_profit", "by_month", "packages"):
        assert key in stats


def test_error_as_value_for_missing_student(tools):
    result = tools.execute("get_student", {"student_id": "000000000000000000000000"})
    assert "error" in result
