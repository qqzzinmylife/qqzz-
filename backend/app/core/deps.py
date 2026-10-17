from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.customer.models import Customer

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError(ErrorCode.UNAUTHENTICATED, "未登录", status_code=401)

    payload = decode_access_token(credentials.credentials)
    user = db.get(User, payload.user_id)
    if user is None or user.status != "active":
        raise AppError(ErrorCode.UNAUTHENTICATED, "登录状态无效", status_code=401)
    return user


def require_merchant(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "merchant":
        raise AppError(ErrorCode.FORBIDDEN, "需要商家权限", status_code=403)
    return user


def require_bound_customer(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Customer:
    if user.role != "customer":
        raise AppError(ErrorCode.FORBIDDEN, "需要客户身份", status_code=403)

    customer = db.execute(select(Customer).where(Customer.user_id == user.id)).scalar_one_or_none()
    if customer is None:
        raise AppError(ErrorCode.CUSTOMER_NOT_BOUND, "尚未绑定客户档案", status_code=403)
    return customer
