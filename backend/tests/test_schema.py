import ast
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
APP_MODULES_DIR = BACKEND_DIR / "app" / "modules"

EXPECTED_TABLES = {
    "merchant",
    "user",
    "customer",
    "customer_group",
    "customer_address",
    "product_category",
    "product",
    "sku",
    "customer_price",
    "price_change_log",
    "cart",
    "cart_item",
    "orders",
    "order_item",
    "audit_log",
}


def _drop_everything(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in inspector.get_table_names():
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


@pytest.fixture(scope="module")
def alembic_upgraded_db() -> Iterator[Session]:
    url = settings.test_database_url
    assert url, "TEST_DATABASE_URL 未配置"

    engine = create_engine(url)
    _drop_everything(engine)

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    with Session(engine) as session:
        yield session


def test_initial_migration_creates_15_tables(alembic_upgraded_db: Session) -> None:
    tables = set(inspect(alembic_upgraded_db.get_bind()).get_table_names())
    # alembic_version 由 alembic 自己维护，不属于业务表
    assert tables - {"alembic_version"} == EXPECTED_TABLES


def test_orders_amount_columns_are_exact(alembic_upgraded_db: Session) -> None:
    cols = {c["name"] for c in inspect(alembic_upgraded_db.get_bind()).get_columns("orders")}
    assert "total_amount" in cols
    assert {"received_amount", "refund_amount", "paid_amount", "pay_status"} & cols == set()


def test_unique_constraints_exist(alembic_upgraded_db: Session) -> None:
    insp = inspect(alembic_upgraded_db.get_bind())

    def uniques(table: str) -> set[tuple[str, ...]]:
        return {tuple(uc["column_names"]) for uc in insp.get_unique_constraints(table)}

    # 唯一约束也可能以唯一索引的形式存在
    def unique_indexes(table: str) -> set[tuple[str, ...]]:
        return {
            tuple(ix["column_names"])
            for ix in insp.get_indexes(table)
            if ix.get("unique")
        }

    def all_unique(table: str) -> set[tuple[str, ...]]:
        return uniques(table) | unique_indexes(table)

    assert ("openid",) in all_unique("user")
    assert ("order_no",) in all_unique("orders")
    assert ("idempotency_key",) in all_unique("orders")
    assert ("customer_id", "sku_id") in all_unique("customer_price")
    assert ("cart_id", "sku_id") in all_unique("cart_item")


def find_cross_module_data_imports() -> list[str]:
    violations: list[str] = []
    for path in sorted(APP_MODULES_DIR.glob("*/*.py")):
        current_module = path.parent.name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            parts = node.module.split(".")
            if len(parts) >= 4 and parts[0] == "app" and parts[1] == "modules":
                target_module, layer = parts[2], parts[3]
                if layer in {"models", "repository"} and target_module != current_module:
                    violations.append(f"{path.name} -> {node.module}")
    return violations


def test_no_module_imports_another_modules_data_layer() -> None:
    assert find_cross_module_data_imports() == []
