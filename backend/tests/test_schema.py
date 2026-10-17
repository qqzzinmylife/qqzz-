import ast
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

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


def test_initial_migration_creates_15_tables(test_engine: Engine) -> None:
    tables = set(inspect(test_engine).get_table_names())
    # alembic_version 由 alembic 自己维护，不属于业务表
    assert tables - {"alembic_version"} == EXPECTED_TABLES


def test_orders_amount_columns_are_exact(test_engine: Engine) -> None:
    cols = {c["name"] for c in inspect(test_engine).get_columns("orders")}
    assert "total_amount" in cols
    assert {"received_amount", "refund_amount", "paid_amount", "pay_status"} & cols == set()


def test_price_change_log_is_append_only(test_engine: Engine) -> None:
    """价格变更日志只追加，时间语义由 changed_at 承担，不该带 created_at/updated_at。"""
    cols = {c["name"] for c in inspect(test_engine).get_columns("price_change_log")}
    assert "changed_at" in cols
    assert "created_at" not in cols
    assert "updated_at" not in cols


def test_unique_constraints_exist(test_engine: Engine) -> None:
    insp = inspect(test_engine)

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
