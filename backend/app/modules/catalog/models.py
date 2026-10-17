from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigInt, TimestampMixin


class ProductCategory(Base, TimestampMixin):
    __tablename__ = "product_category"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInt)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="product_category_status"), nullable=False, default="active"
    )


class Product(Base, TimestampMixin):
    """商品本身不存价格，价格全部在 SKU 上。"""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    category_id: Mapped[int | None] = mapped_column(BigInt, ForeignKey("product_category.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    images: Mapped[list | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(20))
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("on_sale", "off_shelf", name="product_status"), nullable=False, default="on_sale"
    )


class Sku(Base, TimestampMixin):
    """每件商品至少一个 SKU，单规格商品也建一个默认 SKU。"""

    __tablename__ = "sku"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("product.id"), nullable=False, index=True
    )
    spec_name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", name="sku_status"), nullable=False, default="active"
    )
