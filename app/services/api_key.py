import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.api_key import ApiKey


def _generate_raw_key() -> str:
    return f"swor_live_{secrets.token_urlsafe(32)}"


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_api_key(db: AsyncSession, user_id: str, name: str | None = None) -> tuple[ApiKey, str]:
    raw = _generate_raw_key()
    key_hash = _hash_key(raw)
    prefix = raw[:16]

    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=prefix,
        name=name,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw


async def get_api_key_by_raw(db: AsyncSession, raw: str) -> ApiKey | None:
    key_hash = _hash_key(raw)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True))
    key = result.scalar_one_or_none()
    if key:
        key.last_used_at = datetime.now(timezone.utc)
        key.requests_count += 1
        await db.commit()
    return key


async def list_user_keys(db: AsyncSession, user_id: str) -> list[ApiKey]:
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == user_id))
    return list(result.scalars().all())


async def revoke_key(db: AsyncSession, key_id: str, user_id: str) -> bool:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id))
    key = result.scalar_one_or_none()
    if not key:
        return False
    key.is_active = False
    await db.commit()
    return True
