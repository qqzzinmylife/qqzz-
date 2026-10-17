from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def get_by_openid(db: Session, openid: str) -> User | None:
    return db.execute(select(User).where(User.openid == openid)).scalar_one_or_none()


def create_user(
    db: Session,
    *,
    openid: str,
    role: str,
    nickname: str | None = None,
    avatar_url: str | None = None,
) -> User:
    user = User(openid=openid, role=role, nickname=nickname, avatar_url=avatar_url)
    db.add(user)
    db.flush()
    return user
