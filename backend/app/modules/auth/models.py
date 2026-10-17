from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class User(Base, TimestampMixin):
    """登录身份：微信 openid + 角色。客户档案与订单都不挂 openid。"""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    unionid: Mapped[str | None] = mapped_column(String(64))
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(
        Enum("customer", "merchant", name="user_role"), nullable=False, default="customer"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="user_status"), nullable=False, default="active"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
