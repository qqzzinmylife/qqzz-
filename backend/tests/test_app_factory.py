from fastapi.testclient import TestClient

from app.main import create_app


def test_docs_enabled_in_local():
    client = TestClient(create_app(app_env="local"))

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_disabled_outside_local():
    client = TestClient(create_app(app_env="prod"))

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_health_still_available_outside_local():
    client = TestClient(create_app(app_env="prod"))

    assert client.get("/api/v1/health").json() == {"status": "ok"}
