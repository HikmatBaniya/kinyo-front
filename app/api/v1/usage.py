from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.plans import get_plan_limit
from app.models.user import User, PLAN_LIMITS
from app.models.usage_log import UsageLog
from app.api.v1.deps import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageSummary(BaseModel):
    total_requests: int
    total_characters: int
    chars_used_this_period: int
    chars_limit_this_period: int
    chars_remaining: int
    plan: str
    period_reset_at: datetime | None


class UsageLogOut(BaseModel):
    id: str
    characters_used: int
    voice_id: str | None
    model_id: str | None
    output_format: str | None
    source: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SourceBreakdown(BaseModel):
    source: str
    requests: int
    characters: int


@router.get("/summary", response_model=UsageSummary)
async def usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(UsageLog.id),
            func.coalesce(func.sum(UsageLog.characters_used), 0),
        ).where(UsageLog.user_id == current_user.id)
    )
    count, chars = result.one()
    limit = get_plan_limit(current_user.plan)
    used = current_user.chars_used_this_period

    return UsageSummary(
        total_requests=count,
        total_characters=chars,
        chars_used_this_period=used,
        chars_limit_this_period=limit,
        chars_remaining=max(0, limit - used),
        plan=current_user.plan.value,
        period_reset_at=current_user.billing_period_start,
    )


@router.get("/breakdown", response_model=list[SourceBreakdown])
async def usage_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            UsageLog.source,
            func.count(UsageLog.id),
            func.coalesce(func.sum(UsageLog.characters_used), 0),
        )
        .where(UsageLog.user_id == current_user.id)
        .group_by(UsageLog.source)
    )
    return [
        SourceBreakdown(source=row[0], requests=row[1], characters=row[2])
        for row in result.all()
    ]


@router.get("/logs", response_model=list[UsageLogOut])
async def usage_logs(
    limit: int = Query(50, le=200),
    source: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(UsageLog).where(UsageLog.user_id == current_user.id)
    if source:
        q = q.where(UsageLog.source == source)
    q = q.order_by(UsageLog.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())
