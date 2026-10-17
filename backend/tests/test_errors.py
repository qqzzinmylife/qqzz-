from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import AppError, ErrorCode, register_exception_handlers


def test_unknown_route_returns_not_found(client):
    resp = client.get("/api/v1/nope")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
    assert resp.json()["message"] == "请求的资源不存在"


def test_method_not_allowed_returns_chinese_message(client):
    resp = client.post("/api/v1/health")
    assert resp.status_code == 405
    assert resp.json()["code"] == "INVALID_ARGUMENT"
    assert resp.json()["message"] == "请求方法不被支持"


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
    assert resp.json()["message"] == "参数校验失败"


def test_app_error_message_is_passed_through():
    probe = FastAPI()
    register_exception_handlers(probe)

    @probe.get("/boom")
    def _boom():
        raise AppError(ErrorCode.INVALID_ARGUMENT, "客户专属价必须大于 0")

    resp = TestClient(probe).get("/boom")
    assert resp.status_code == 400
    assert resp.json()["message"] == "客户专属价必须大于 0"


def test_custom_http_exception_detail_is_preserved():
    probe = FastAPI()
    register_exception_handlers(probe)

    @probe.get("/custom")
    def _custom():
        raise HTTPException(status_code=400, detail="这个客户已经绑定过了")

    resp = TestClient(probe).get("/custom")
    assert resp.status_code == 400
    assert resp.json()["message"] == "这个客户已经绑定过了"
