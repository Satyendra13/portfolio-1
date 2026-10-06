import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "dev-secret-key-change-in-production-32bytes"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./asistline.db"
    DATABASE_URL_SYNC: str = "sqlite:///./asistline.db"

    # LiveKit
    LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "secret"

    # AI Models
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_ID: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_STT_MODEL: str = "scribe_v1"
    ELEVENLABS_TTS_MODEL: str = "eleven_multilingual_v2"

    # Defaults & Thresholds
    DEFAULT_KB_MIN_SCORE: float = 0.55
    DEFAULT_QUEUE_TIMEOUT_SECONDS: int = 45
    DEFAULT_SILENCE_TIMEOUT_SECONDS: float = 6.0

    MOCK_BACKENDS_URL: str = "http://localhost:9000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
