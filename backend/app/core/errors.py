from enum import StrEnum
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


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.INVALID_ARGUMENT,
    }.get(exc.status_code, ErrorCode.INVALID_ARGUMENT)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return error_response(exc.status_code, code, message)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
