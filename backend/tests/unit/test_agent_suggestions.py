"""AI 助手配套接口测试：建议问题（状态候选+个性化排序）、提问记录、用户记忆。

跑法（与 CI 一致用独立库）：DB_NAME=easy_book_test uv run pytest tests/unit/test_agent_suggestions.py -v
"""
import pytest
import pytest_asyncio

from api_server.database import get_database
from api_server import auth


@pytest_asyncio.fixture
async def clean_agent_db():
    db = get_database()
    await db.db.agent_queries.delete_many({})
    await db.db.agent_memory.delete_many({})
    yield db
    await db.db.agent_queries.delete_many({})
    await db.db.agent_memory.delete_many({})
    await db.db.students.delete_many({})
    await db.db.packages.delete_many({})


def _unwrap(body: dict):
    """兼容两种响应风格：学员接口直接返回对象，套餐接口带 {code,data} 信封。"""
    return body.get("data") if isinstance(body, dict) and "data" in body else body


async def _make_student_with_package(client, name: str, remaining: int):
    stu = _unwrap((await client.post("/api/students/", json={"name": name})).json())
    await client.post("/api/packages/", json={
        "student_id": stu["id"],
        "name": "测试课包",
        "package_type": "count_based",
        "price": 100.0,
        "venue_share": 0.0,
        "count_based_info": {"total_lessons": remaining, "remaining_lessons": remaining},
    })
    return stu


@pytest.mark.asyncio
async def test_suggestions_include_low_balance_first(client, clean_agent_db):
    """有学员课时 ≤3 → 续课提醒排第一并点名该学员。"""
    await _make_student_with_package(client, "李冬梅", remaining=2)
    resp = await client.get("/api/agent/suggestions")
    assert resp.status_code == 200
    suggestions = resp.json()["data"]["suggestions"]
    assert len(suggestions) == 3
    assert suggestions[0]["intent"] == "low_balance"
    assert "李冬梅" in suggestions[0]["message"]


@pytest.mark.asyncio
async def test_suggestions_fallback_when_empty(client, clean_agent_db):
    """空库 → 返回 3 条通用兜底建议。"""
    resp = await client.get("/api/agent/suggestions")
    suggestions = resp.json()["data"]["suggestions"]
    assert len(suggestions) == 3
    assert all(s["message"] for s in suggestions)


@pytest.mark.asyncio
async def test_suggestions_personalized_by_query_history(client, clean_agent_db):
    """用户常问营收 → 营收建议对该用户排序上升（对比匿名用户）。"""
    for _ in range(3):
        await client.post("/api/agent/queries", json={
            "user_id": "coach1", "text": "这个月收入多少", "intent": "monthly_profit"})
    anon = (await client.get("/api/agent/suggestions")).json()["data"]["suggestions"]
    mine = (await client.get("/api/agent/suggestions", params={"user_id": "coach1"})).json()["data"]["suggestions"]
    anon_rank = next(i for i, s in enumerate(anon) if s["intent"] == "monthly_profit")
    my_rank = next(i for i, s in enumerate(mine) if s["intent"] == "monthly_profit")
    assert my_rank <= anon_rank
    assert next(s["score"] for s in mine if s["intent"] == "monthly_profit") > \
           next(s["score"] for s in anon if s["intent"] == "monthly_profit")


@pytest.mark.asyncio
async def test_query_log_rejects_empty_text(client, clean_agent_db):
    resp = await client.post("/api/agent/queries", json={"user_id": "u", "text": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_memory_create_dedup_list_delete(client, clean_agent_db):
    """记忆：创建→重复创建去重→列表→软删除。"""
    body = {"user_id": "coach1", "kind": "person",
            "content": "小红是张钰桐的小名", "source": "user_explicit", "confidence": 0.9}
    r1 = (await client.post("/api/agent/memories", json=body)).json()["data"]
    assert r1["dedup"] is False
    r2 = (await client.post("/api/agent/memories", json=body)).json()["data"]
    assert r2["dedup"] is True and r2["id"] == r1["id"]

    listed = (await client.get("/api/agent/memories", params={"user_id": "coach1"})).json()["data"]["memories"]
    assert len(listed) == 1 and listed[0]["content"] == "小红是张钰桐的小名"

    await client.delete(f"/api/agent/memories/{r1['id']}")
    listed = (await client.get("/api/agent/memories", params={"user_id": "coach1"})).json()["data"]["memories"]
    assert listed == []


@pytest.mark.asyncio
async def test_memory_kind_validation(client, clean_agent_db):
    resp = await client.post("/api/agent/memories", json={
        "user_id": "u", "kind": "nonsense", "content": "x"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_auth_check_returns_user_id_header(client, monkeypatch):
    """启用鉴权时 /api/auth/check 响应头带 X-User-Id（nginx 透传给 Chainlit 用）。"""
    monkeypatch.setenv("EASY_BOOK_AUTH", "1")
    token = auth.create_token("13800001234")
    resp = await client.get("/api/auth/check", cookies={"eb_token": token})
    assert resp.status_code == 200
    assert resp.headers.get("x-user-id") == "13800001234"
