from pydantic import BaseModel, Field
from enum import Enum


class AudioFormat(str, Enum):
    mp3 = "mp3_44100_128"
    mp3_high = "mp3_44100_192"
    pcm = "pcm_44100"
    ulaw = "ulaw_8000"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str | None = None
    model_id: str = "eleven_multilingual_v2"
    output_format: AudioFormat = AudioFormat.mp3
    stability: float = Field(0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0)
    style: float = Field(0.0, ge=0.0, le=1.0)
    use_speaker_boost: bool = True


class BatchTTSItem(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str | None = None


class BatchTTSRequest(BaseModel):
    items: list[BatchTTSItem] = Field(..., min_length=1, max_length=10)
    model_id: str = "eleven_multilingual_v2"
    output_format: AudioFormat = AudioFormat.mp3


class VoiceOut(BaseModel):
    voice_id: str
    name: str
    preview_url: str | None
    labels: dict | None


class BatchTTSResult(BaseModel):
    index: int
    text: str
    success: bool
    audio_base64: str | None = None
    error: str | None = None
    characters_used: int = 0
