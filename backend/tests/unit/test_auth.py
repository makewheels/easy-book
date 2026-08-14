"""
认证鉴权测试：令牌/密码哈希 + 登录接口 + 接口保护 + 用户来源标记 sourceType
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from api_server import auth
from api_server.data_source import normalize_source_type
from api_server.database import get_database

TEST_PHONE = "13800000001"
TEST_PASSWORD = "auth-test-password-123"
TEST_SERVICE_KEY = "auth-test-service-key"


@pytest.fixture
def force_auth(monkeypatch):
    monkeypatch.setenv("EASY_BOOK_AUTH", "1")
    monkeypatch.setenv("EASY_BOOK_JWT_SECRET", "unit-test-secret")
    monkeypatch.setenv("EASY_BOOK_SERVICE_KEY", TEST_SERVICE_KEY)
    yield
    monkeypatch.delenv("EASY_BOOK_AUTH", raising=False)


@pytest_asyncio.fixture
async def test_user():
    db = get_database().db
    await db.users.delete_many({"phone": TEST_PHONE})
    await db.users.insert_one({
        "phone": TEST_PHONE,
        "password_hash": auth.hash_password(TEST_PASSWORD),
    })
    yield TEST_PHONE
    await db.users.delete_many({"phone": TEST_PHONE})


class TestToken:
    def test_roundtrip(self):
        token = auth.create_token("alice")
        assert auth.verify_token(token) == "alice"

    def test_tampered_signature_rejected(self):
        token = auth.create_token("alice")
        body, _sig = token.rsplit(".", 1)
        assert auth.verify_token(f"{body}.{'0' * 64}") is None

    def test_expired_rejected(self, monkeypatch):
        monkeypatch.setattr(auth, "TOKEN_TTL_SECONDS", -1)
        token = auth.create_token("alice")
        assert auth.verify_token(token) is None

    def test_malformed_rejected(self):
        assert auth.verify_token("not-a-token") is None
        assert auth.verify_token("") is None


class TestPasswordHash:
    def test_verify_correct(self):
        stored = auth.hash_password("secret123")
        assert auth.verify_password("secret123", stored) is True

    def test_verify_wrong(self):
        stored = auth.hash_password("secret123")
        assert auth.verify_password("wrong", stored) is False
        assert auth.verify_password("secret123", "garbage") is False

    def test_unique_salt(self):
        assert auth.hash_password("same") != auth.hash_password("same")


@pytest.mark.asyncio
class TestAuthAPI:
    """开启鉴权（EASY_BOOK_AUTH=1）时的接口行为"""

    async def test_login_success(self, client: AsyncClient, force_auth, test_user):
        resp = await client.post("/api/auth/login", json={"phone": TEST_PHONE, "password": TEST_PASSWORD})
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == TEST_PHONE
        assert auth.verify_token(data["token"]) == TEST_PHONE
        # 未标记来源的用户默认按真实用户处理
        assert data["sourceType"] == "human"

    async def test_login_ai_test_source(self, client: AsyncClient, force_auth):
        db = get_database().db
        await db.users.delete_many({"phone": TEST_PHONE})
        await db.users.insert_one({
            "phone": TEST_PHONE,
            "password_hash": auth.hash_password(TEST_PASSWORD),
            "sourceType": "ai_test",
        })
        try:
            resp = await client.post("/api/auth/login", json={"phone": TEST_PHONE, "password": TEST_PASSWORD})
            assert resp.status_code == 200
            assert resp.json()["sourceType"] == "ai_test"
        finally:
            await db.users.delete_many({"phone": TEST_PHONE})

    async def test_login_wrong_password(self, client: AsyncClient, force_auth, test_user):
        resp = await client.post("/api/auth/login", json={"phone": TEST_PHONE, "password": "wrong"})
        assert resp.status_code == 401

    async def test_protected_requires_auth(self, client: AsyncClient, force_auth):
        resp = await client.get("/api/stats/lessons")
        assert resp.status_code == 401

    async def test_protected_with_token(self, client: AsyncClient, force_auth, test_user):
        login = await client.post("/api/auth/login", json={"phone": TEST_PHONE, "password": TEST_PASSWORD})
        token = login.json()["token"]
        resp = await client.get("/api/stats/lessons", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    async def test_protected_with_service_key(self, client: AsyncClient, force_auth):
        resp = await client.get("/api/stats/lessons", headers={"X-Service-Key": TEST_SERVICE_KEY})
        assert resp.status_code == 200

    async def test_check_cookie_valid(self, client: AsyncClient, force_auth, test_user):
        login = await client.post("/api/auth/login", json={"phone": TEST_PHONE, "password": TEST_PASSWORD})
        token = login.json()["token"]
        resp = await client.get("/api/auth/check", cookies={"eb_token": token})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    async def test_check_cookie_missing_or_invalid(self, client: AsyncClient, force_auth):
        assert (await client.get("/api/auth/check")).status_code == 401
        assert (await client.get("/api/auth/check", cookies={"eb_token": "bad"})).status_code == 401

    async def test_health_stays_open(self, client: AsyncClient, force_auth):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_dev_mode_open_by_default(self, client: AsyncClient, monkeypatch):
        monkeypatch.delenv("EASY_BOOK_AUTH", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        resp = await client.get("/api/stats/lessons")
        assert resp.status_code == 200


class TestSourceType:
    """用户来源标记（human/ai_test）"""

    def test_normalize_defaults_to_human(self):
        assert normalize_source_type(None) == "human"
        assert normalize_source_type("") == "human"
        assert normalize_source_type("unknown") == "human"
        assert normalize_source_type("human") == "human"

    def test_normalize_ai_test(self):
        assert normalize_source_type("ai_test") == "ai_test"

    @pytest.mark.asyncio
    async def test_ensure_admin_user_marks_source(self, monkeypatch):
        phone = "13900009999"
        db = get_database().db
        await db.users.delete_many({"phone": phone})
        monkeypatch.setenv("ADMIN_PHONE", phone)
        monkeypatch.setenv("ADMIN_PASSWORD", "seed-password")
        monkeypatch.setenv("ADMIN_SOURCE_TYPE", "ai_test")
        try:
            await auth.ensure_admin_user()
            user = await db.users.find_one({"phone": phone})
            assert user["sourceType"] == "ai_test"
            # 再次运行不重复创建，且校正来源标记
            monkeypatch.setenv("ADMIN_SOURCE_TYPE", "human")
            await auth.ensure_admin_user()
            assert await db.users.count_documents({"phone": phone}) == 1
            user = await db.users.find_one({"phone": phone})
            assert user["sourceType"] == "human"
        finally:
            await db.users.delete_many({"phone": phone})
