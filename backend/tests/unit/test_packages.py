"""
套餐管理 API 单元测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPackageAPI:
    """套餐 CRUD API 测试"""

    async def _create_student(self, client: AsyncClient) -> str:
        """辅助方法：创建一个测试学员并返回 ID"""
        resp = await client.post("/api/students/", json={
            "name": "套餐测试学员",
            "learning_item": "自由泳"
        })
        return resp.json()["id"]

    async def test_create_count_based_package(self, client: AsyncClient, clean_db):
        """创建记次套餐"""
        student_id = await self._create_student(client)
        resp = await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "10次自由泳课",
            "package_type": "1v1",
            "price": 2000,
            "venue_share": 500,
            "count_based_info": {
                "total_lessons": 10,
                "remaining_lessons": 10
            }
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "10次自由泳课"
        assert data["package_type"] == "1v1"
        assert data["count_based_info"]["total_lessons"] == 10
        assert data["count_based_info"]["remaining_lessons"] == 10

    async def test_create_time_based_package(self, client: AsyncClient, clean_db):
        """创建时长套餐"""
        student_id = await self._create_student(client)
        resp = await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "月卡",
            "package_type": "time_based",
            "price": 3000,
            "venue_share": 800,
            "time_based_info": {
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["time_based_info"]["start_date"] == "2026-01-01"

    async def test_get_student_packages(self, client: AsyncClient, clean_db):
        """获取学员套餐列表"""
        student_id = await self._create_student(client)
        # 创建两个套餐
        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "套餐A",
            "package_type": "1v1",
            "price": 1000,
            "venue_share": 300,
            "count_based_info": {"total_lessons": 5, "remaining_lessons": 5}
        })
        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "套餐B",
            "package_type": "1v2",
            "price": 800,
            "venue_share": 200,
            "count_based_info": {"total_lessons": 8, "remaining_lessons": 8}
        })

        resp = await client.get(f"/api/packages/?student_id={student_id}")
        assert resp.status_code == 200
        packages = resp.json()
        assert len(packages) == 2

    async def test_student_aggregated_lessons(self, client: AsyncClient, clean_db):
        """学员 API 返回聚合课时 — 创建套餐后学员的 remaining_lessons 和 total_lessons 应更新"""
        student_id = await self._create_student(client)

        # 创建两个记次套餐
        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "套餐1",
            "package_type": "1v1",
            "price": 1000,
            "venue_share": 300,
            "count_based_info": {"total_lessons": 10, "remaining_lessons": 8}
        })
        await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "套餐2",
            "package_type": "1v2",
            "price": 800,
            "venue_share": 200,
            "count_based_info": {"total_lessons": 5, "remaining_lessons": 5}
        })

        # 获取学员详情
        resp = await client.get(f"/api/students/{student_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_lessons"] == 15   # 10 + 5
        assert data["remaining_lessons"] == 13  # 8 + 5

    async def test_student_no_packages_lessons_zero(self, client: AsyncClient, clean_db):
        """没有套餐的学员 — 课时聚合为 0"""
        student_id = await self._create_student(client)
        resp = await client.get(f"/api/students/{student_id}")
        data = resp.json()
        assert data["total_lessons"] == 0
        assert data["remaining_lessons"] == 0

    async def test_create_package_missing_fields(self, client: AsyncClient, clean_db):
        """创建套餐 — 缺少必填字段"""
        student_id = await self._create_student(client)
        resp = await client.post("/api/packages/", json={
            "student_id": student_id,
            "name": "不完整套餐"
            # 缺少 package_type, price, venue_share
        })
        assert resp.status_code == 422
