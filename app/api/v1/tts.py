import base64
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.plans import get_plan_limit, maybe_reset_usage
from app.models.user import User
from app.models.usage_log import UsageLog
from app.schemas.tts import TTSRequest, BatchTTSRequest, BatchTTSResult, VoiceOut, AudioFormat
from app.services.elevenlabs import generate_speech, generate_speech_raw, list_voices, get_user_info
from app.api.v1.deps import get_current_user, get_user_from_api_key
import httpx

router = APIRouter(prefix="/tts", tags=["tts"])


async def _check_and_deduct(user: User, char_count: int, db: AsyncSession) -> int:
    """Check quota, deduct chars, return remaining. Raises 429 if exceeded."""
    await maybe_reset_usage(user, db)
    limit = get_plan_limit(user.plan)
    if user.chars_used_this_period + char_count > limit:
        remaining = max(0, limit - user.chars_used_this_period)
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit reached. {remaining} chars remaining on {user.plan} plan.",
        )
    user.chars_used_this_period += char_count
    return get_plan_limit(user.plan) - user.chars_used_this_period


async def _log(db: AsyncSession, user_id: str, req: TTSRequest, source: str, api_key_id: str | None = None):
    db.add(UsageLog(
        user_id=user_id,
        api_key_id=api_key_id,
        characters_used=len(req.text),
        voice_id=req.voice_id,
        model_id=req.model_id,
        output_format=req.output_format.value,
        source=source,
    ))
    await db.commit()


async def _synthesize(user: User, req: TTSRequest, db: AsyncSession, source: str, api_key_id: str | None = None) -> Response:
    remaining = await _check_and_deduct(user, len(req.text), db)
    try:
        audio, mime = await generate_speech(req)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {e.response.text}")

    await _log(db, user.id, req, source, api_key_id)
    limit = get_plan_limit(user.plan)

    return Response(
        content=audio,
        media_type=mime,
        headers={
            "X-Chars-Used": str(user.chars_used_this_period),
            "X-Chars-Limit": str(limit),
            "X-Chars-Remaining": str(remaining),
            "X-Plan": user.plan.value,
        },
    )


@router.post("/synthesize", summary="Synthesize speech (dashboard)")
async def synthesize_dashboard(
    req: TTSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _synthesize(current_user, req, db, source="dashboard")


@router.post("/synthesize/external", summary="Synthesize speech (API key)")
async def synthesize_api(
    req: TTSRequest,
    api_user: User = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    External API endpoint. Authenticate with `X-API-Key` header.
    Returns audio/mpeg binary. Response headers include quota info.
    """
    return await _synthesize(api_user, req, db, source="api")


@router.post("/batch/external", response_model=list[BatchTTSResult], summary="Batch synthesize (API key)")
async def batch_synthesize_api(
    req: BatchTTSRequest,
    api_user: User = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Synthesize up to 10 texts in one call. Returns base64-encoded audio per item.
    Characters across all items count toward your monthly quota.
    """
    await maybe_reset_usage(api_user, db)
    limit = get_plan_limit(api_user.plan)
    total_chars = sum(len(item.text) for item in req.items)

    if api_user.chars_used_this_period + total_chars > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Batch requires {total_chars} chars but only {limit - api_user.chars_used_this_period} remaining.",
        )

    results: list[BatchTTSResult] = []
    for i, item in enumerate(req.items):
        try:
            audio = await generate_speech_raw(
                text=item.text,
                voice_id=item.voice_id,
                model_id=req.model_id,
                output_format=req.output_format,
            )
            results.append(BatchTTSResult(
                index=i,
                text=item.text,
                success=True,
                audio_base64=base64.b64encode(audio).decode(),
                characters_used=len(item.text),
            ))
            api_user.chars_used_this_period += len(item.text)
            db.add(UsageLog(
                user_id=api_user.id,
                characters_used=len(item.text),
                voice_id=item.voice_id,
                model_id=req.model_id,
                output_format=req.output_format.value,
                source="api_batch",
            ))
        except httpx.HTTPStatusError as e:
            results.append(BatchTTSResult(
                index=i, text=item.text, success=False,
                error=f"ElevenLabs error: {e.response.status_code}",
            ))

    await db.commit()
    return results


@router.get("/voices", response_model=list[VoiceOut], summary="List available voices")
async def voices(current_user: User = Depends(get_current_user)):
    try:
        return await list_voices()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {e.response.text}")


@router.get("/voices/external", response_model=list[VoiceOut], summary="List voices (API key)")
async def voices_external(api_user: User = Depends(get_user_from_api_key)):
    try:
        return await list_voices()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {e.response.text}")


@router.get("/health", summary="ElevenLabs quota info")
async def elevenlabs_health(current_user: User = Depends(get_current_user)):
    try:
        info = await get_user_info()
        sub = info.get("subscription", {})
        return {
            "status": "ok",
            "tier": sub.get("tier"),
            "character_count": sub.get("character_count"),
            "character_limit": sub.get("character_limit"),
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {e.response.text}")
