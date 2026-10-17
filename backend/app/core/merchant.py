from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy import select

from app.db.base import Base, BigInt, TimestampMixin


class Merchant(Base, TimestampMixin):
    """商家档案。第一版只有一条记录，供小票抬头与页面展示使用。"""

    __tablename__ = "merchant"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="merchant_status"), nullable=False, default="active"
    )


def get_merchant(db: Session) -> Merchant | None:
    """单商家模式下取唯一那条商家档案。"""
    return db.execute(select(Merchant).order_by(Merchant.id).limit(1)).scalar_one_or_none()
