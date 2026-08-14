"""认证鉴权：登录发令牌 + 接口保护。

- 仅生产环境默认启用（ENVIRONMENT=production）；EASY_BOOK_AUTH=1/0 可强制覆盖
- 两种凭据：
  1. Bearer 令牌：/api/auth/login 成功后获得（HMAC-SHA256 签名，12 小时有效）
  2. X-Service-Key：服务间调用（agent→backend），值为 EASY_BOOK_SERVICE_KEY
- 管理员账号由 ADMIN_USERNAME/ADMIN_PASSWORD 在启动时自动创建（scrypt 哈希存储）
- 零额外依赖：签名令牌与密码哈希均用标准库实现
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel, Field

from api_server.database import get_database
from api_server.data_source import normalize_source_type

TOKEN_TTL_SECONDS = 12 * 3600

router = APIRouter(tags=["认证"])


# ── 开关 ──────────────────────────────────────────────────────


def auth_enabled() -> bool:
    override = os.getenv("EASY_BOOK_AUTH")
    if override is not None:
        return override.lower() in ("1", "true", "yes")
    return os.getenv("ENVIRONMENT") == "production"


# ── 签名令牌（HMAC-SHA256） ──────────────────────────────────


def _jwt_secret() -> bytes:
    secret = os.getenv("EASY_BOOK_JWT_SECRET", "") or "easy-book-dev-secret"
    return secret.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_token(username: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_jwt_secret(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_token(token: str) -> Optional[str]:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(_jwt_secret(), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64url_decode(body))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    return payload.get("sub")


# ── 密码哈希（scrypt） ───────────────────────────────────────


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return hmac.compare_digest(dk.hex(), dk_hex)


# ── 用户存取（手机号为用户标识） ─────────────────────────────


async def get_user(phone: str) -> Optional[dict]:
    db = get_database().db
    return await db.users.find_one({"phone": phone})


async def ensure_admin_user() -> None:
    """启动时按环境变量创建管理员账号；已存在则校正其来源标记（sourceType）。

    来源由 ADMIN_SOURCE_TYPE 指定（human/ai_test，默认 human）。测试账号标成
    ai_test 后，其名下数据即可被评测识别为测试数据。
    """
    phone = os.getenv("ADMIN_PHONE")
    password = os.getenv("ADMIN_PASSWORD")
    if not phone or not password:
        if auth_enabled():
            raise RuntimeError("鉴权已启用但未配置 ADMIN_PHONE / ADMIN_PASSWORD")
        return
    source_type = normalize_source_type(os.getenv("ADMIN_SOURCE_TYPE"))
    db = get_database().db
    existing = await get_user(phone)
    if existing is None:
        await db.users.insert_one({
            "phone": phone,
            "password_hash": hash_password(password),
            "sourceType": source_type,
            "create_time": datetime.now(timezone.utc).isoformat(),
        })
        print(f"已创建管理员账号: {phone} (sourceType={source_type})")
    elif existing.get("sourceType") != source_type:
        await db.users.update_one({"phone": phone}, {"$set": {"sourceType": source_type}})
        print(f"已校正管理员账号来源标记: {phone} -> {source_type}")


# ── 登录接口 ─────────────────────────────────────────────────


class LoginRequest(BaseModel):
    phone: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login")
async def login(req: LoginRequest):
    user = await get_user(req.phone)
    if user is None or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    return {
        "token": create_token(req.phone),
        "phone": req.phone,
        "sourceType": normalize_source_type(user.get("sourceType")),
        "expires_in": TOKEN_TTL_SECONDS,
    }


# Cookie 名：前端登录后写入，nginx auth_request 用它做 /ai 的会话拦截
TOKEN_COOKIE_NAME = "eb_token"


@router.get("/check")
async def check_session(eb_token: Optional[str] = Cookie(default=None)):
    """供 nginx auth_request 调用：校验会话 cookie，200=已登录，401=未登录。"""
    if not auth_enabled():
        return {"valid": True}
    if eb_token and verify_token(eb_token):
        return {"valid": True}
    raise HTTPException(status_code=401, detail="未登录或凭据无效")


# ── 接口保护依赖 ─────────────────────────────────────────────


async def require_auth(request: Request) -> None:
    if not auth_enabled():
        return
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and verify_token(auth_header[7:]):
        return
    service_key = os.getenv("EASY_BOOK_SERVICE_KEY", "")
    provided = request.headers.get("X-Service-Key", "")
    if service_key and provided and hmac.compare_digest(service_key, provided):
        return
    raise HTTPException(status_code=401, detail="未登录或凭据无效")
