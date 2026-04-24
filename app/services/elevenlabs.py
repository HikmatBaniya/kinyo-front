import httpx
from app.core.config import get_settings
from app.schemas.tts import TTSRequest, VoiceOut, AudioFormat

settings = get_settings()

BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"

FORMAT_MIME = {
    AudioFormat.mp3: "audio/mpeg",
    AudioFormat.mp3_high: "audio/mpeg",
    AudioFormat.pcm: "audio/wav",
    AudioFormat.ulaw: "audio/basic",
}


def _headers() -> dict:
    return {"xi-api-key": settings.elevenlabs_api_key}


async def generate_speech(req: TTSRequest) -> tuple[bytes, str]:
    """Returns (audio_bytes, mime_type)."""
    voice_id = req.voice_id or DEFAULT_VOICE_ID
    mime = FORMAT_MIME.get(req.output_format, "audio/mpeg")
    payload = {
        "text": req.text,
        "model_id": req.model_id,
        "voice_settings": {
            "stability": req.stability,
            "similarity_boost": req.similarity_boost,
            "style": req.style,
            "use_speaker_boost": req.use_speaker_boost,
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}/text-to-speech/{voice_id}",
            params={"output_format": req.output_format.value},
            headers={**_headers(), "Accept": mime, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.content, mime


async def generate_speech_raw(
    text: str,
    voice_id: str | None,
    model_id: str,
    output_format: AudioFormat,
) -> bytes:
    voice_id = voice_id or DEFAULT_VOICE_ID
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}/text-to-speech/{voice_id}",
            params={"output_format": output_format.value},
            headers={**_headers(), "Accept": "audio/mpeg", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.content


async def list_voices() -> list[VoiceOut]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/voices", headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return [
            VoiceOut(
                voice_id=v["voice_id"],
                name=v["name"],
                preview_url=v.get("preview_url"),
                labels=v.get("labels"),
            )
            for v in data.get("voices", [])
        ]


async def get_user_info() -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/user", headers=_headers())
        resp.raise_for_status()
        return resp.json()
