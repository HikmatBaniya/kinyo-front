from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User, Plan
from app.api.v1.deps import get_current_user
from pydantic import BaseModel

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/billing", tags=["billing"])

PLAN_PRICE_MAP = {
    "starter": settings.stripe_price_starter,
    "pro": settings.stripe_price_pro,
    "enterprise": settings.stripe_price_enterprise,
}

PRICE_PLAN_MAP = {
    settings.stripe_price_starter: Plan.starter,
    settings.stripe_price_pro: Plan.pro,
    settings.stripe_price_enterprise: Plan.enterprise,
}


class CheckoutRequest(BaseModel):
    plan: str  # "starter" | "pro" | "enterprise"


@router.post("/checkout")
async def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    price_id = PLAN_PRICE_MAP.get(payload.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {payload.plan}")
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing not configured")

    try:
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id},
            )
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.app_url}/dashboard/billing?success=1",
            cancel_url=f"{settings.app_url}/dashboard/billing?canceled=1",
            metadata={"user_id": current_user.id, "plan": payload.plan},
        )
        return {"url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/portal")
async def customer_portal(current_user: User = Depends(get_current_user)):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing not configured")

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.app_url}/dashboard/billing",
        )
        return {"url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        plan_name = session["metadata"].get("plan")
        customer_id = session.get("customer")
        sub_id = session.get("subscription")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and plan_name:
            user.plan = Plan(plan_name)
            user.stripe_customer_id = customer_id
            user.stripe_subscription_id = sub_id
            await db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user:
            user.plan = Plan.free
            user.stripe_subscription_id = None
            await db.commit()

    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        price_id = sub["items"]["data"][0]["price"]["id"] if sub.get("items") else None
        new_plan = PRICE_PLAN_MAP.get(price_id)

        result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user and new_plan:
            user.plan = new_plan
            await db.commit()

    return {"status": "ok"}
