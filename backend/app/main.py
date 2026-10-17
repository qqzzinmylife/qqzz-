from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import add_request_id_middleware, setup_logging
from app.modules.auth.router import router as auth_router

setup_logging()


def create_app(*, app_env: str | None = None) -> FastAPI:
    """按环境装配应用。接口文档只在本地开放（规格第 10 节）。"""
    env = settings.app_env if app_env is None else app_env
    docs_enabled = env == "local"

    app = FastAPI(
        title="shop-backend",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    add_request_id_middleware(app)
    register_exception_handlers(app)
    app.include_router(auth_router)

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
