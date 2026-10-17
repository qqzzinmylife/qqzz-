from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.core.audit  # noqa: F401  注册 audit_log
import app.core.merchant  # noqa: F401  注册 merchant
import app.modules.auth.models  # noqa: F401
import app.modules.cart.models  # noqa: F401
import app.modules.catalog.models  # noqa: F401
import app.modules.customer.models  # noqa: F401
import app.modules.order.models  # noqa: F401
import app.modules.pricing.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 优先用调用方显式设置的 URL（测试会指向 shoper_test），否则回落到应用配置
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
