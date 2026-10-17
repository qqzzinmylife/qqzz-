import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BACKEND_DIR = Path(__file__).resolve().parents[1]

# 仓库里没有 .env 时，用测试默认值把 Settings 撑起来；一旦存在 .env，
# 就完全交给它（避免 os.environ 遮蔽 pydantic-settings 读到的 .env 值）。
if not (_BACKEND_DIR / ".env").exists():
    os.environ.setdefault("DATABASE_URL", "mysql+pymysql://root:root@127.0.0.1:3306/shoper?charset=utf8mb4")
    os.environ.setdefault("TEST_DATABASE_URL", "mysql+pymysql://root:root@127.0.0.1:3306/shoper_test?charset=utf8mb4")
    os.environ.setdefault("JWT_SECRET", "test-secret")

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
