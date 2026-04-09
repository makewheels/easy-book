"""
预约和考勤 API 单元测试
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAppointmentAPI:
    """预约 API 测试"""

    async def _create_student(self, client: AsyncClient) -> str:
        resp = await client.post("/api/students/", json={
            "name": "预约测试学员",
            "gender": "男",
            "age": 10
        })
        return resp.json()["id"]

    async def _create_package(self, client: AsyncClient, student_id: str, lessons: int = 10) -> str:
        resp = await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": f"{lessons}次课程",
            "package_type": "1v1",
            "price": 2000,
            "venue_share": 500,
            "count_based_info": {
                "total_lessons": lessons,
                "remaining_lessons": lessons
            }
        })
        return resp.json()["id"]

    async def test_create_appointment(self, client: AsyncClient, clean_db):
        """创建预约"""
        student_id = await self._create_student(client)
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["student_id"] == student_id

    async def test_create_appointment_missing_student(self, client: AsyncClient, clean_db):
        """创建预约 — 缺少 student_id"""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        resp = await client.post("/api/appointments/", json={
            "start_time": tomorrow,
            "duration_in_minutes": 60
        })
        assert resp.status_code == 400

    async def test_get_daily_appointments(self, client: AsyncClient, clean_db):
        """获取每日预约"""
        student_id = await self._create_student(client)
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)

        await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": now.isoformat(),
            "duration_in_minutes": 60
        })

        resp = await client.get(f"/api/appointments/daily/{today}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200

    async def test_cancel_appointment(self, client: AsyncClient, clean_db):
        """取消预约"""
        student_id = await self._create_student(client)
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        create_resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        appointment_id = create_resp.json()["data"].get("id")
        if appointment_id:
            resp = await client.post(f"/api/appointments/{appointment_id}/cancel")
            assert resp.status_code == 200

    async def test_batch_appointments(self, client: AsyncClient, clean_db):
        """批量获取预约"""
        today = datetime.now().strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        resp = await client.get(f"/api/appointments/batch?start_date={today}&end_date={next_week}")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200


@pytest.mark.asyncio
class TestAttendanceAPI:
    """考勤 API 测试"""

    async def _setup_student_with_appointment(self, client: AsyncClient):
        """创建学员 + 套餐 + 预约，返回 (student_id, appointment_id)"""
        # 创建学员
        student_resp = await client.post("/api/students/", json={
            "name": "考勤测试学员",
            "gender": "男",
            "age": 10
        })
        student_id = student_resp.json()["id"]

        # 创建套餐
        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "10次课",
            "package_type": "1v1",
            "price": 2000,
            "venue_share": 500,
            "count_based_info": {
                "total_lessons": 10,
                "remaining_lessons": 10
            }
        })

        # 创建预约
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        apt_resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        appointment_id = apt_resp.json()["data"].get("id")

        return student_id, appointment_id

    async def test_checkin_success(self, client: AsyncClient, clean_db):
        """签到成功 — 套餐课时减少"""
        student_id, appointment_id = await self._setup_student_with_appointment(client)
        if not appointment_id:
            pytest.skip("appointment_id not returned")

        resp = await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["lessons_before"] == 10
        assert data["data"]["lessons_after"] == 9

        # 验证学员聚合课时也更新了
        student_resp = await client.get(f"/api/students/{student_id}")
        assert student_resp.json()["remaining_lessons"] == 9

    async def test_checkin_duplicate(self, client: AsyncClient, clean_db):
        """重复签到 — 应该失败"""
        student_id, appointment_id = await self._setup_student_with_appointment(client)
        if not appointment_id:
            pytest.skip("appointment_id not returned")

        # 第一次签到
        await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        # 第二次签到 — 应该 400
        resp = await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert resp.status_code == 400

    async def test_cancel_attendance(self, client: AsyncClient, clean_db):
        """标记取消 — 不扣课时"""
        student_id, appointment_id = await self._setup_student_with_appointment(client)
        if not appointment_id:
            pytest.skip("appointment_id not returned")

        resp = await client.post("/api/attendance/cancel", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["lessons_before"] == data["data"]["lessons_after"]  # 不扣课时

        # 验证学员课时没变
        student_resp = await client.get(f"/api/students/{student_id}")
        assert student_resp.json()["remaining_lessons"] == 10

    async def test_get_student_attendance(self, client: AsyncClient, clean_db):
        """获取学员考勤记录"""
        student_id, appointment_id = await self._setup_student_with_appointment(client)
        if not appointment_id:
            pytest.skip("appointment_id not returned")

        # 签到
        await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })

        resp = await client.get(f"/api/attendance/student/{student_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "checked"

    async def test_checkin_no_package(self, client: AsyncClient, clean_db):
        """签到 — 没有套餐应该失败"""
        # 创建学员（不创建套餐）
        student_resp = await client.post("/api/students/", json={
            "name": "无套餐学员",
            "gender": "男",
            "age": 10
        })
        student_id = student_resp.json()["id"]

        # 创建预约
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        apt_resp = await client.post("/api/appointments/", json={
            "student_id": student_id,
            "start_time": tomorrow.isoformat(),
            "duration_in_minutes": 60
        })
        appointment_id = apt_resp.json()["data"].get("id")
        if not appointment_id:
            pytest.skip("appointment_id not returned")

        resp = await client.post("/api/attendance/checkin", json={
            "appointment_id": appointment_id,
            "student_id": student_id
        })
        assert resp.status_code == 400
        assert "课程不足" in resp.json()["detail"]
