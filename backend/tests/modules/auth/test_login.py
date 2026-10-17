from app.core.config import settings
from app.core.security import create_access_token
from app.modules.auth.models import User

from tests.helpers import auth, count_rows


def test_first_login_creates_user(client, db_session, wechat_stub):
    wechat_stub.openid = "openid-a"

    resp = client.post("/api/v1/auth/login", json={"code": "c1"})

    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"
    assert resp.json()["need_bind"] is True
    assert count_rows(db_session, User) == 1


def test_second_login_reuses_user(client, db_session, wechat_stub):
    wechat_stub.openid = "openid-b"

    first = client.post("/api/v1/auth/login", json={"code": "c1"})
    second = client.post("/api/v1/auth/login", json={"code": "c2"})

    assert first.json()["role"] == second.json()["role"] == "customer"
    assert count_rows(db_session, User) == 1


def test_merchant_role_from_env_openid(client, wechat_stub, monkeypatch):
    monkeypatch.setattr(settings, "merchant_openid", "openid-merchant")
    wechat_stub.openid = "openid-merchant"

    resp = client.post("/api/v1/auth/login", json={"code": "c"})

    assert resp.json()["role"] == "merchant"
    assert resp.json()["need_bind"] is False


def test_expired_token_returns_401(client, db_session):
    user = User(openid="openid-expired", role="customer", status="active")
    db_session.add(user)
    db_session.flush()
    token = create_access_token(user.id, "customer", expires_in_minutes=-1)

    resp = client.get("/api/v1/auth/profile", headers=auth(token))

    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHENTICATED"


def test_tampered_token_returns_401(client, db_session):
    user = User(openid="openid-tampered", role="customer", status="active")
    db_session.add(user)
    db_session.flush()
    token = create_access_token(user.id, "customer")
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    resp = client.get("/api/v1/auth/profile", headers=auth(tampered))

    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHENTICATED"
