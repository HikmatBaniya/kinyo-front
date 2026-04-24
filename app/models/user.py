import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class Plan(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class Role(str, enum.Enum):
    user = "user"
    admin = "admin"


PLAN_LIMITS = {
    Plan.free:       {"chars_per_month": 10_000,     "max_api_keys": 1,  "price_usd": 0},
    Plan.starter:    {"chars_per_month": 100_000,    "max_api_keys": 3,  "price_usd": 19},
    Plan.pro:        {"chars_per_month": 500_000,    "max_api_keys": 10, "price_usd": 79},
    Plan.enterprise: {"chars_per_month": 10_000_000, "max_api_keys": 50, "price_usd": 299},
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    organization: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.user)
    plan: Mapped[Plan] = mapped_column(SAEnum(Plan), default=Plan.free)

    # Billing
    stripe_customer_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    billing_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Usage tracking (current billing period)
    chars_used_this_period: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    usage_logs: Mapped[list["UsageLog"]] = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
