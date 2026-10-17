from enum import StrEnum
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    CUSTOMER_NOT_BOUND = "CUSTOMER_NOT_BOUND"
    NOT_FOUND = "NOT_FOUND"
    PRICE_CHANGED = "PRICE_CHANGED"
    ORDER_STATE_INVALID = "ORDER_STATE_INVALID"
    VALIDATION_ERROR = "VALIDATION_ERROR"


# 框架自己抛出的 HTTPException（404、405 等）带的是英文短语，
# 这里按状态码给出中文文案；业务侧自己写的 detail 仍然原样透出。
_STATUS_MESSAGES: dict[int, str] = {
    400: "请求参数有误",
    401: "登录状态无效或已过期",
    403: "没有访问权限",
    404: "请求的资源不存在",
    405: "请求方法不被支持",
    406: "无法满足请求的响应格式",
    408: "请求超时",
    409: "当前状态不允许该操作",
    413: "请求内容过大",
    415: "不支持的请求数据格式",
    422: "参数校验失败",
    429: "请求过于频繁，请稍后重试",
    500: "服务器内部错误",
    502: "上游服务异常",
    503: "服务暂时不可用",
}
_DEFAULT_STATUS_MESSAGE = "请求处理失败"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        detail: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


def error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    detail: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": str(code), "message": message, "detail": detail},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.detail)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        422,
        ErrorCode.VALIDATION_ERROR,
        "参数校验失败",
        {"errors": jsonable_encoder(exc.errors())},
    )


def _is_default_status_phrase(status_code: int, detail: str) -> bool:
    try:
        return HTTPStatus(status_code).phrase == detail
    except ValueError:
        return False


def _http_message(exc: StarletteHTTPException) -> str:
    detail = exc.detail
    if (
        isinstance(detail, str)
        and detail
        and not _is_default_status_phrase(exc.status_code, detail)
    ):
        return detail
    return _STATUS_MESSAGES.get(exc.status_code, _DEFAULT_STATUS_MESSAGE)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.INVALID_ARGUMENT,
    }.get(exc.status_code, ErrorCode.INVALID_ARGUMENT)
    return error_response(exc.status_code, code, _http_message(exc))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
