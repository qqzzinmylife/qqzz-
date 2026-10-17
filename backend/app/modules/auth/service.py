from dataclasses import dataclass
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.security import create_access_token
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.customer import service as customer_service

WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


@dataclass(frozen=True)
class LoginResult:
    token: str
    role: str
    need_bind: bool


@dataclass(frozen=True)
class ProfileResult:
    user_id: int
    role: str
    need_bind: bool
    customer_id: int | None


def fetch_openid(code: str) -> str:
    """用 code 换 openid。测试里由 wechat_stub 替换掉。"""
    response = httpx.get(
        WECHAT_CODE2SESSION_URL,
        params={
            "appid": settings.wechat_appid,
            "secret": settings.wechat_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        },
        timeout=5.0,
    )
    response.raise_for_status()
    data = response.json()
    openid = data.get("openid")
    if not openid:
        raise AppError(
            ErrorCode.UNAUTHENTICATED,
            f"微信登录失败：{data.get('errmsg', 'unknown error')}",
            status_code=401,
        )
    return openid


def _resolve_role(user: User) -> str:
    """MERCHANT_OPENID 命中的身份始终是商家，顺带修复历史数据。"""
    if settings.merchant_openid and user.openid == settings.merchant_openid:
        user.role = "merchant"
    return user.role


def login_by_wx(db: Session, code: str) -> LoginResult:
    openid = fetch_openid(code)

    user = repository.get_by_openid(db, openid)
    if user is None:
        role = "merchant" if openid and openid == settings.merchant_openid else "customer"
        user = repository.create_user(db, openid=openid, role=role)

    role = _resolve_role(user)
    user.last_login_at = datetime.now()
    db.commit()

    customer_id = customer_service.find_bound_customer_id(db, user.id)
    return LoginResult(
        token=create_access_token(user.id, role),
        role=role,
        need_bind=role == "customer" and customer_id is None,
    )


def get_user(db: Session, user_id: int) -> User | None:
    """按 id 取登录身份，供鉴权依赖使用。"""
    return repository.get_by_id(db, user_id)


def build_profile(db: Session, user: User) -> ProfileResult:
    customer_id = customer_service.find_bound_customer_id(db, user.id)
    return ProfileResult(
        user_id=user.id,
        role=user.role,
        need_bind=user.role == "customer" and customer_id is None,
        customer_id=customer_id,
    )
