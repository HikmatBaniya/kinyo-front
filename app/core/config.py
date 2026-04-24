from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Swor Nepali TTS API"
    app_version: str = "0.1.0"
    debug: bool = False

    # ElevenLabs
    elevenlabs_api_key: str

    # Database
    database_url: str

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""   # Stripe Price ID for starter plan
    stripe_price_pro: str = ""       # Stripe Price ID for pro plan
    stripe_price_enterprise: str = ""

    # App URL (for Stripe redirects)
    app_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
