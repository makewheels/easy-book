"""
学员管理 API 单元测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestStudentAPI:
    """学员 CRUD API 测试"""

    async def test_create_student_success(self, client: AsyncClient, clean_db):
        """创建学员 — 正常流程"""
        resp = await client.post("/api/students/", json={
            "name": "张三",
            "learning_item": "自由泳"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "张三"
        assert data["learning_item"] == "自由泳"
        assert data["id"] is not None
        assert data["remaining_lessons"] is None  # 没有套餐时为 None
        assert data["total_lessons"] is None

    async def test_create_student_with_phone(self, client: AsyncClient, clean_db):
        """创建学员 — 带电话号码"""
        resp = await client.post("/api/students/", json={
            "name": "李四",
            "learning_item": "蛙泳",
            "phone": "13800138000"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "13800138000"

    async def test_create_student_with_notes(self, client: AsyncClient, clean_db):
        """创建学员 — 带备注"""
        resp = await client.post("/api/students/", json={
            "name": "王五",
            "learning_item": "仰泳",
            "notes": "怕水，需要特别关注"
        })
        assert resp.status_code == 200
        assert resp.json()["notes"] == "怕水，需要特别关注"

    async def test_create_student_missing_name(self, client: AsyncClient, clean_db):
        """创建学员 — 缺少必填字段 name"""
        resp = await client.post("/api/students/", json={
            "learning_item": "自由泳"
        })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_create_student_missing_learning_item(self, client: AsyncClient, clean_db):
        """创建学员 — 缺少必填字段 learning_item"""
        resp = await client.post("/api/students/", json={
            "name": "赵六"
        })
        assert resp.status_code == 422

    async def test_create_student_empty_name(self, client: AsyncClient, clean_db):
        """创建学员 — 空名字应该失败"""
        resp = await client.post("/api/students/", json={
            "name": "",
            "learning_item": "自由泳"
        })
        assert resp.status_code == 422

    async def test_get_students_empty(self, client: AsyncClient, clean_db):
        """获取学员列表 — 空列表"""
        resp = await client.get("/api/students/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_students_after_create(self, client: AsyncClient, clean_db):
        """获取学员列表 — 创建后能查到"""
        await client.post("/api/students/", json={
            "name": "测试学员A",
            "learning_item": "自由泳"
        })
        await client.post("/api/students/", json={
            "name": "测试学员B",
            "learning_item": "蛙泳"
        })
        resp = await client.get("/api/students/")
        assert resp.status_code == 200
        students = resp.json()
        assert len(students) == 2
        names = {s["name"] for s in students}
        assert "测试学员A" in names
        assert "测试学员B" in names

    async def test_get_student_by_id(self, client: AsyncClient, clean_db):
        """根据 ID 获取学员"""
        create_resp = await client.post("/api/students/", json={
            "name": "单查学员",
            "learning_item": "蝶泳"
        })
        student_id = create_resp.json()["id"]

        resp = await client.get(f"/api/students/{student_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "单查学员"

    async def test_get_student_not_found(self, client: AsyncClient, clean_db):
        """获取不存在的学员 — 404"""
        resp = await client.get("/api/students/000000000000000000000000")
        assert resp.status_code == 404

    async def test_update_student(self, client: AsyncClient, clean_db):
        """更新学员信息"""
        create_resp = await client.post("/api/students/", json={
            "name": "原始名",
            "learning_item": "自由泳"
        })
        student_id = create_resp.json()["id"]

        resp = await client.put(f"/api/students/{student_id}", json={
            "name": "新名字",
            "notes": "新增备注"
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名字"
        assert resp.json()["notes"] == "新增备注"

    async def test_update_student_not_found(self, client: AsyncClient, clean_db):
        """更新不存在的学员 — 404"""
        resp = await client.put("/api/students/000000000000000000000000", json={
            "name": "不存在"
        })
        assert resp.status_code == 404

    async def test_delete_student(self, client: AsyncClient, clean_db):
        """删除学员"""
        create_resp = await client.post("/api/students/", json={
            "name": "待删学员",
            "learning_item": "自由泳"
        })
        student_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/students/{student_id}")
        assert resp.status_code == 200

        # 验证已删除
        get_resp = await client.get(f"/api/students/{student_id}")
        assert get_resp.status_code == 404

    async def test_delete_student_not_found(self, client: AsyncClient, clean_db):
        """删除不存在的学员 — 404"""
        resp = await client.delete("/api/students/000000000000000000000000")
        assert resp.status_code == 404
