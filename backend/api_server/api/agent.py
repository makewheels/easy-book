"""AI 助手配套接口：建议问题、提问记录（习惯统计）、用户记忆。

设计见 docs/agent-memory-and-suggestions.md。集合：
- agent_queries  每次提问的意图记录（个性化排序的依据）
- agent_memory   分类型用户记忆（preference/fact/person/process/pattern）
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api_server.database import get_database
from api_server.services.suggestions import SuggestionService

router = APIRouter()

MEMORY_KINDS = {"preference", "fact", "person", "process", "pattern"}
MEMORY_SOURCES = {"llm_extract", "user_explicit", "rule"}
MEMORY_PER_USER_CAP = 200


def _ok(data=None, message: str = "成功"):
    return {"code": 200, "message": message, "data": data}


# ── 建议问题 ────────────────────────────────────────────────


@router.get("/suggestions")
async def get_suggestions(user_id: str = "", limit: int = 3):
    """开场/跟进建议：系统状态候选 + 该用户习惯排序。"""
    limit = max(1, min(limit, 5))
    suggestions = await SuggestionService.build_suggestions(user_id=user_id, limit=limit)
    return _ok({"suggestions": suggestions})


# ── 提问记录（习惯统计）──────────────────────────────────────


class QueryLogRequest(BaseModel):
    user_id: str = ""
    text: str = Field(min_length=1, max_length=2000)
    intent: str = ""          # 由 agent 侧按工具映射；空=未识别
    tools: list[str] = Field(default_factory=list)


@router.post("/queries")
async def log_query(req: QueryLogRequest):
    db = get_database().db
    await db.agent_queries.insert_one({
        "user_id": req.user_id,
        "text": req.text,
        "intent": req.intent or "general",
        "tools": req.tools,
        "create_time": datetime.now(),
    })
    return _ok()


# ── 用户记忆 ────────────────────────────────────────────────


class MemoryCreateRequest(BaseModel):
    user_id: str = ""
    kind: str
    content: str = Field(min_length=1, max_length=500)
    source: str = "llm_extract"
    confidence: float = Field(default=0.8, ge=0, le=1)


@router.get("/memories")
async def list_memories(user_id: str = ""):
    """某用户的有效记忆（按更新时间倒序）；user_id 空 → 全局记忆。"""
    db = get_database().db
    cursor = db.agent_memory.find(
        {"user_id": user_id, "status": "active"}
    ).sort("update_time", -1)
    memories = []
    async for doc in cursor:
        memories.append({
            "id": str(doc["_id"]),
            "user_id": doc.get("user_id", ""),
            "kind": doc["kind"],
            "content": doc["content"],
            "source": doc.get("source", ""),
            "confidence": doc.get("confidence", 0.8),
            "use_count": doc.get("use_count", 0),
            "create_time": doc.get("create_time"),
            "update_time": doc.get("update_time"),
        })
    return _ok({"memories": memories})


@router.post("/memories")
async def create_memory(req: MemoryCreateRequest):
    if req.kind not in MEMORY_KINDS:
        raise HTTPException(status_code=400, detail=f"kind 必须是 {sorted(MEMORY_KINDS)}")
    if req.source not in MEMORY_SOURCES:
        raise HTTPException(status_code=400, detail=f"source 必须是 {sorted(MEMORY_SOURCES)}")
    db = get_database().db
    now = datetime.now()
    # 去重：同用户同类型同内容 → 只提升置信度与更新时间
    existing = await db.agent_memory.find_one(
        {"user_id": req.user_id, "kind": req.kind, "content": req.content})
    if existing:
        await db.agent_memory.update_one({"_id": existing["_id"]}, {"$set": {
            "confidence": max(existing.get("confidence", 0), req.confidence),
            "update_time": now,
        }})
        return _ok({"id": str(existing["_id"]), "dedup": True})

    result = await db.agent_memory.insert_one({
        "user_id": req.user_id,
        "kind": req.kind,
        "content": req.content,
        "source": req.source,
        "confidence": req.confidence,
        "use_count": 0,
        "status": "active",
        "create_time": now,
        "update_time": now,
    })
    await _enforce_cap(db, req.user_id)
    return _ok({"id": str(result.inserted_id), "dedup": False})


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """软删除（保留记录，便于审计）。"""
    from bson import ObjectId
    db = get_database().db
    result = await db.agent_memory.update_one(
        {"_id": ObjectId(memory_id)}, {"$set": {"status": "deleted", "update_time": datetime.now()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return _ok()


async def _enforce_cap(db, user_id: str) -> None:
    """每用户最多保留 MEMORY_PER_USER_CAP 条有效记忆，超出删最旧的。"""
    count = await db.agent_memory.count_documents({"user_id": user_id, "status": "active"})
    overflow = count - MEMORY_PER_USER_CAP
    if overflow <= 0:
        return
    ids = []
    async for doc in db.agent_memory.find(
            {"user_id": user_id, "status": "active"}
    ).sort("update_time", 1).limit(overflow):
        ids.append(doc["_id"])
    await db.agent_memory.update_many(
        {"_id": {"$in": ids}}, {"$set": {"status": "deleted"}})
