from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import AppError, ErrorCode


class TokenPayload(BaseModel):
    user_id: int
    role: str


def create_access_token(
    user_id: int, role: str, expires_in_minutes: int | None = None
) -> str:
    minutes = settings.jwt_expire_minutes if expires_in_minutes is None else expires_in_minutes
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(user_id=int(payload["sub"]), role=str(payload["role"]))
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise AppError(ErrorCode.UNAUTHENTICATED, "登录状态无效或已过期", status_code=401) from exc
