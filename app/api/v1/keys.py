from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.plans import get_max_keys
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut, ApiKeyCreated
from app.services.api_key import create_api_key, list_user_keys, revoke_key
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await list_user_keys(db, current_user.id)
    active = [k for k in existing if k.is_active]
    max_keys = get_max_keys(current_user.plan)

    if len(active) >= max_keys:
        raise HTTPException(
            status_code=403,
            detail=f"Plan limit: {max_keys} active API keys on {current_user.plan} plan. Upgrade to create more.",
        )

    key_obj, raw = await create_api_key(db, current_user.id, payload.name)
    return ApiKeyCreated(
        id=key_obj.id,
        key_prefix=key_obj.key_prefix,
        name=key_obj.name,
        is_active=key_obj.is_active,
        requests_count=key_obj.requests_count,
        created_at=key_obj.created_at,
        last_used_at=key_obj.last_used_at,
        key=raw,
    )


@router.get("", response_model=list[ApiKeyOut])
async def get_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_user_keys(db, current_user.id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await revoke_key(db, key_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
