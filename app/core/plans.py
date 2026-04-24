from datetime import datetime, timezone
from app.models.user import Plan, PLAN_LIMITS


def get_plan_limit(plan: Plan) -> int:
    return PLAN_LIMITS[plan]["chars_per_month"]


def get_max_keys(plan: Plan) -> int:
    return PLAN_LIMITS[plan]["max_api_keys"]


def is_period_expired(period_start: datetime | None) -> bool:
    if not period_start:
        return True
    now = datetime.now(timezone.utc)
    delta = now - period_start
    return delta.days >= 30


def should_reset_usage(user) -> bool:
    return is_period_expired(user.billing_period_start)


async def maybe_reset_usage(user, db) -> None:
    """Reset character count if billing period has rolled over."""
    if should_reset_usage(user):
        user.chars_used_this_period = 0
        user.billing_period_start = datetime.now(timezone.utc)
        await db.commit()
