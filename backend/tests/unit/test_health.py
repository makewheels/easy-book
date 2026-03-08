"""
健康检查和基础 API 测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthAPI:
    """健康检查接口测试"""

    async def test_root(self, client: AsyncClient):
        """根路径返回欢迎消息"""
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "running" in resp.json()["message"].lower() or "Easy Book" in resp.json()["message"]

    async def test_health(self, client: AsyncClient):
        """健康检查"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_db_health(self, client: AsyncClient):
        """数据库健康检查"""
        resp = await client.get("/api/health/db")
        assert resp.status_code == 200
        assert resp.json()["database"] == "healthy"
