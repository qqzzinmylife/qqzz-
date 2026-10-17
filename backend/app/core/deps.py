from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.models import User
from app.modules.customer import service as customer_service
from app.modules.customer.models import Customer

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError(ErrorCode.UNAUTHENTICATED, "未登录", status_code=401)

    payload = decode_access_token(credentials.credentials)
    user = auth_service.get_user(db, payload.user_id)
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

    customer = customer_service.find_bound_customer(db, user.id)
    if customer is None:
        raise AppError(ErrorCode.CUSTOMER_NOT_BOUND, "尚未绑定客户档案", status_code=403)
    return customer
