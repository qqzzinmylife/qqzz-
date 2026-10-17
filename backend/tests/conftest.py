import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

_BACKEND_DIR = Path(__file__).resolve().parents[1]

# 仓库里没有 .env 时，用测试默认值把 Settings 撑起来；一旦存在 .env，
# 就完全交给它（避免 os.environ 遮蔽 pydantic-settings 读到的 .env 值）。
if not (_BACKEND_DIR / ".env").exists():
    os.environ.setdefault(
        "DATABASE_URL", "mysql+pymysql://root:root@127.0.0.1:3306/shoper?charset=utf8mb4"
    )
    os.environ.setdefault(
        "TEST_DATABASE_URL", "mysql+pymysql://root:root@127.0.0.1:3306/shoper_test?charset=utf8mb4"
    )
    os.environ.setdefault("JWT_SECRET", "test-secret")

from app.core.config import settings  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _drop_everything(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in inspector.get_table_names():
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    """整轮测试共用一个已迁移到 head 的测试库。"""
    url = settings.test_database_url
    assert url, "TEST_DATABASE_URL 未配置"

    engine = create_engine(url, poolclass=NullPool)
    _drop_everything(engine)

    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """每个用例一个外层事务，结束时回滚，用例之间互不污染。"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """接口测试一律打在测试库上：把 get_db 换成上面那个事务性 session。"""

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def wechat_stub(monkeypatch: pytest.MonkeyPatch):
    """替换微信 code2Session，测试不发真实网络请求。"""
    from app.modules.auth import service as auth_service

    class WechatStub:
        openid = "openid-default"
        code_to_openid: dict[str, str] = {}

    stub = WechatStub()

    def _fetch_openid(code: str) -> str:
        return stub.code_to_openid.get(code, stub.openid)

    monkeypatch.setattr(auth_service, "fetch_openid", _fetch_openid)
    return stub


