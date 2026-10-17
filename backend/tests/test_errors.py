from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import register_exception_handlers


def test_unknown_route_returns_not_found(client):
    resp = client.get("/api/v1/nope")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


def test_validation_error_is_wrapped():
    probe = FastAPI()
    register_exception_handlers(probe)

    class ProbePayload(BaseModel):
        code: str

    @probe.post("/probe")
    def _probe(payload: ProbePayload) -> dict[str, str]:
        return {"code": payload.code}

    resp = TestClient(probe).post("/probe", json={})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
