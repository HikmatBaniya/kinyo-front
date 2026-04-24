from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import Plan, Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    organization: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    organization: str | None
    plan: Plan
    role: Role
    is_active: bool
    is_verified: bool
    chars_used_this_period: int
    billing_period_start: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
