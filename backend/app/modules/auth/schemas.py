from pydantic import BaseModel


class LoginRequest(BaseModel):
    code: str


class LoginResponse(BaseModel):
    token: str
    role: str
    need_bind: bool


class ProfileResponse(BaseModel):
    user_id: int
    role: str
    need_bind: bool
    customer_id: int | None
