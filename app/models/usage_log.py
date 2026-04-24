import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    api_key_id: Mapped[str | None] = mapped_column(String, ForeignKey("api_keys.id"), nullable=True)
    characters_used: Mapped[int] = mapped_column(Integer, nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String, nullable=True)
    model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    output_format: Mapped[str | None] = mapped_column(String, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String, default="dashboard")  # "dashboard" | "api"
    status: Mapped[str] = mapped_column(String, default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="usage_logs")
