from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class Cart(Base, TimestampMixin):
    __tablename__ = "cart"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("customer.id"), nullable=False, unique=True
    )
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_item"
    __table_args__ = (UniqueConstraint("cart_id", "sku_id", name="uq_cart_item_cart_sku"),)

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(BigInt, ForeignKey("cart.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInt, ForeignKey("sku.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
