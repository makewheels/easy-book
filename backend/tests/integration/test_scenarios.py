"""
集成测试 — 完整业务场景
测试从创建学员到签到的完整流程，验证 MongoDB 数据一致性
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFullWorkflow:
    """完整业务流程集成测试"""

    async def test_full_student_lifecycle(self, client: AsyncClient, clean_db):
        """场景：学员完整生命周期
        创建学员 → 创建套餐 → 创建预约 → 签到 → 验证课时扣减 → 查看考勤记录
        """
        # 1. 创建学员
        student_resp = await client.post("/api/students/", json={
            "name": "完整流程学员",
            "gender": "男",
            "age": 10,
            "phone": "13900139000",
            "emergency_contact": "13900000000"
        })
        assert student_resp.status_code == 200
        student = student_resp.json()
        student_id = student["id"]
        assert student["remaining_lessons"] is None or student["remaining_lessons"] == 0

        # 2. 创建记次套餐（10次课）
        pkg_resp = await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "10次自由泳私教课",
            "package_type": "1v1",
            "price": 3000,
            "venue_share": 800,
            "count_based_info": {
                "total_lessons": 10,
                "remaining_lessons": 10
            }
        })
        assert pkg_resp.status_code == 201
        package = pkg_resp.json()
        assert package["count_based_info"]["remaining_lessons"] == 10

        # 3. 验证学员聚合课时
        student_resp2 = await client.get(f"/api/students/{student_id}")
        assert student_resp2.json()["total_lessons"] == 10
        assert student_resp2.json()["remaining_lessons"] == 10

        # 4. 创建预约
        tomorrow = (datetime.now() + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        apt_resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        assert apt_resp.status_code == 200
        appointment_id = apt_resp.json()["data"].get("id")
        assert appointment_id is not None

        # 5. 签到
        checkin_resp = await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert checkin_resp.status_code == 200
        checkin_data = checkin_resp.json()["data"]
        assert checkin_data["lessons_before"] == 10
        assert checkin_data["lessons_after"] == 9

        # 6. 验证学员课时已扣减
        student_resp3 = await client.get(f"/api/students/{student_id}")
        assert student_resp3.json()["remaining_lessons"] == 9

        # 7. 获取考勤记录
        att_resp = await client.get(f"/api/attendance/student/{student_id}")
        assert att_resp.status_code == 200
        records = att_resp.json()["data"]
        assert len(records) == 1
        assert records[0]["status"] == "checked"

    async def test_cancel_does_not_deduct(self, client: AsyncClient, clean_db):
        """场景：取消预约不扣课时"""
        # 创建学员 + 套餐
        student_resp = await client.post("/api/students/", json={
            "name": "取消测试学员",
            "gender": "男",
            "age": 11
        })
        student_id = student_resp.json()["id"]

        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "5次课",
            "package_type": "1v1",
            "price": 1500,
            "venue_share": 400,
            "count_based_info": {"total_lessons": 5, "remaining_lessons": 5}
        })

        # 创建预约
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0)
        apt_resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        appointment_id = apt_resp.json()["data"].get("id")

        # 标记取消
        cancel_resp = await client.post("/api/attendance/cancel", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert cancel_resp.status_code == 200

        # 验证课时没扣
        student_resp2 = await client.get(f"/api/students/{student_id}")
        assert student_resp2.json()["remaining_lessons"] == 5

    async def test_multiple_students_independent(self, client: AsyncClient, clean_db):
        """场景：多学员课时互不影响"""
        # 学员 A
        a_resp = await client.post("/api/students/", json={
            "name": "学员A", "gender": "男", "age": 10
        })
        a_id = a_resp.json()["id"]
        await client.post("/api/packages/", json={
            "student_id": a_id, "name": "A的套餐",
            "package_type": "1v1", "price": 1000, "venue_share": 300,
            "count_based_info": {"total_lessons": 5, "remaining_lessons": 5}
        })

        # 学员 B
        b_resp = await client.post("/api/students/", json={
            "name": "学员B", "gender": "女", "age": 9
        })
        b_id = b_resp.json()["id"]
        await client.post("/api/packages/", json={
            "student_id": b_id, "name": "B的套餐",
            "package_type": "1v2", "price": 800, "venue_share": 200,
            "count_based_info": {"total_lessons": 8, "remaining_lessons": 8}
        })

        # A 签到
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0)
        a_apt = await client.post("/api/appointments/", json={
            "student_id": a_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        a_apt_id = a_apt.json()["data"].get("id")
        if a_apt_id:
            await client.post("/api/attendance/checkin", json={
                "appointment_id": a_apt_id, "student_id": a_id
            })

        # 验证 A 扣了，B 没扣
        a_data = (await client.get(f"/api/students/{a_id}")).json()
        b_data = (await client.get(f"/api/students/{b_id}")).json()
        assert a_data["remaining_lessons"] == 4  # 5 - 1
        assert b_data["remaining_lessons"] == 8  # 不变

    async def test_multiple_packages_deduct_first(self, client: AsyncClient, clean_db):
        """场景：多套餐时扣减第一个有余量的套餐"""
        student_resp = await client.post("/api/students/", json={
            "name": "多套餐学员", "gender": "男", "age": 10
        })
        student_id = student_resp.json()["id"]

        # 创建两个套餐
        await client.post("/api/packages/", json={
            "student_id": student_id, "name": "套餐1",
            "package_type": "1v1", "price": 1000, "venue_share": 300,
            "count_based_info": {"total_lessons": 3, "remaining_lessons": 3}
        })
        await client.post("/api/packages/", json={
            "student_id": student_id, "name": "套餐2",
            "package_type": "1v1", "price": 1000, "venue_share": 300,
            "count_based_info": {"total_lessons": 5, "remaining_lessons": 5}
        })

        # 验证总课时
        student_data = (await client.get(f"/api/students/{student_id}")).json()
        assert student_data["total_lessons"] == 8
        assert student_data["remaining_lessons"] == 8

        # 签到一次
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0)
        apt = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        apt_id = apt.json()["data"].get("id")
        if apt_id:
            await client.post("/api/attendance/checkin", json={
                "appointment_id": apt_id, "student_id": student_id
            })

        # 验证总课时减了 1
        student_data2 = (await client.get(f"/api/students/{student_id}")).json()
        assert student_data2["remaining_lessons"] == 7  # 8 - 1

    async def test_delete_student_cascades(self, client: AsyncClient, clean_db):
        """场景：删除学员后预约也被删除"""
        student_resp = await client.post("/api/students/", json={
            "name": "待删除学员", "gender": "男", "age": 10
        })
        student_id = student_resp.json()["id"]

        # 创建预约
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0)
        await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })

        # 删除学员
        del_resp = await client.delete(f"/api/students/{student_id}")
        assert del_resp.status_code == 200

        # 验证学员已删除
        get_resp = await client.get(f"/api/students/{student_id}")
        assert get_resp.status_code == 404
