from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class CustomerGroup(Base, TimestampMixin):
    __tablename__ = "customer_group"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="customer_group_status"), nullable=False, default="active"
    )


class Customer(Base, TimestampMixin):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    group_id: Mapped[int | None] = mapped_column(BigInt, ForeignKey("customer_group.id"))
    user_id: Mapped[int | None] = mapped_column(BigInt, ForeignKey("user.id"), unique=True)
    bind_status: Mapped[str] = mapped_column(
        Enum("unbound", "pending", "bound", "rejected", name="customer_bind_status"),
        nullable=False,
        default="unbound",
    )
    bind_applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    remark: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="customer_status"), nullable=False, default="active"
    )


class CustomerAddress(Base, TimestampMixin):
    __tablename__ = "customer_address"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("customer.id"), nullable=False, index=True
    )
    consignee: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    region: Mapped[str | None] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="customer_address_status"),
        nullable=False,
        default="active",
    )
