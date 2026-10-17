from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, LoginResponse, ProfileResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    result = service.login_by_wx(db, payload.code)
    return LoginResponse(token=result.token, role=result.role, need_bind=result.need_bind)


@router.get("/profile", response_model=ProfileResponse)
def profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    result = service.build_profile(db, user)
    return ProfileResponse(
        user_id=result.user_id,
        role=result.role,
        need_bind=result.need_bind,
        customer_id=result.customer_id,
    )
