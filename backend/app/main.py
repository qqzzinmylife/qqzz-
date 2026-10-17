from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.core.logging import add_request_id_middleware, setup_logging

setup_logging()

app = FastAPI(title="shop-backend", version="0.1.0")

add_request_id_middleware(app)
register_exception_handlers(app)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
