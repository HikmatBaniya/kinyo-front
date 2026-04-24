from pydantic import BaseModel
from datetime import datetime


class ApiKeyCreate(BaseModel):
    name: str | None = None


class ApiKeyOut(BaseModel):
    id: str
    key_prefix: str
    name: str | None
    is_active: bool
    requests_count: int
    created_at: datetime
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class ApiKeyCreated(ApiKeyOut):
    key: str  # only returned once on creation
