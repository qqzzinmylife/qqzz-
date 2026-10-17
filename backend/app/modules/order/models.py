from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class Order(Base, TimestampMixin):
    """订单金额在下单时一次写入并冻结；之后只能改收款与交付状态。"""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_received_at", "received_at"),
        Index("ix_orders_customer_received", "customer_id", "received_at"),
        Index("ix_orders_customer_placed", "customer_id", "placed_at"),
        Index("ix_orders_status_placed", "status", "placed_at"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(BigInt, ForeignKey("customer.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "delivered", "cancelled", name="order_status"),
        nullable=False,
        default="pending",
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime)
    received_by: Mapped[int | None] = mapped_column(BigInt, ForeignKey("user.id"))
    delivery_type: Mapped[str] = mapped_column(
        Enum("pickup", "delivery", name="order_delivery_type"), nullable=False, default="pickup"
    )
    consignee: Mapped[str | None] = mapped_column(String(50))
    consignee_phone: Mapped[str | None] = mapped_column(String(20))
    consignee_address: Mapped[str | None] = mapped_column(String(255))
    remark: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    placed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancel_reason: Mapped[str | None] = mapped_column(String(255))


class OrderItem(Base, TimestampMixin):
    """小票、对账单、营收统计只读这里的快照，不读当前价格。"""

    __tablename__ = "order_item"
    __table_args__ = (Index("ix_order_item_order", "order_id"),)

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInt, ForeignKey("orders.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInt, ForeignKey("sku.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(BigInt, ForeignKey("product.id"), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    spec_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_source: Mapped[str] = mapped_column(
        Enum("customer", "default", name="order_item_price_source"), nullable=False
    )
