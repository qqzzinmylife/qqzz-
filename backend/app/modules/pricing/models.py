from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class CustomerPrice(Base, TimestampMixin):
    """只存「有专属价」的情况；没有记录就是走默认价。"""

    __tablename__ = "customer_price"
    __table_args__ = (
        UniqueConstraint("customer_id", "sku_id", name="uq_customer_price_customer_sku"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(BigInt, ForeignKey("customer.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInt, ForeignKey("sku.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255))


class PriceChangeLog(Base):
    """默认价与客户专属价的变更都写这里；默认价变更时 customer_id 为空。"""

    __tablename__ = "price_change_log"
    __table_args__ = (
        Index("ix_price_change_log_sku_changed", "sku_id", "changed_at"),
        Index("ix_price_change_log_customer_changed", "customer_id", "changed_at"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    price_type: Mapped[str] = mapped_column(
        Enum("default", "customer", name="price_change_type"), nullable=False
    )
    sku_id: Mapped[int] = mapped_column(BigInt, ForeignKey("sku.id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(BigInt, ForeignKey("customer.id"))
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    new_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    change_type: Mapped[str] = mapped_column(
        Enum("create", "update", "reset_default", name="price_change_action"), nullable=False
    )
    operator_id: Mapped[int] = mapped_column(BigInt, ForeignKey("user.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    remark: Mapped[str | None] = mapped_column(String(255))
