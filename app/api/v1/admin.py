from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.user import User, Plan, Role
from app.models.usage_log import UsageLog
from app.api.v1.deps import get_current_user
from app.schemas.user import UserOut
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class PlanUpdate(BaseModel):
    plan: Plan


class UserAdminOut(UserOut):
    role: str
    chars_used_this_period: int
    stripe_customer_id: str | None
    stripe_subscription_id: str | None


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
    return [UserAdminOut.model_validate(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}/plan", response_model=UserAdminOut)
async def update_user_plan(
    user_id: str,
    payload: PlanUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.plan = payload.plan
    await db.commit()
    await db.refresh(user)
    return UserAdminOut.model_validate(user)


@router.patch("/users/{user_id}/toggle-active", response_model=UserAdminOut)
async def toggle_user_active(
    user_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return UserAdminOut.model_validate(user)


@router.get("/stats")
async def platform_stats(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_requests = (await db.execute(select(func.count(UsageLog.id)))).scalar()
    total_chars = (await db.execute(select(func.coalesce(func.sum(UsageLog.characters_used), 0)))).scalar()

    plan_counts = {}
    for plan in Plan:
        count = (await db.execute(select(func.count(User.id)).where(User.plan == plan))).scalar()
        plan_counts[plan.value] = count

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "total_chars_processed": total_chars,
        "users_by_plan": plan_counts,
    }
