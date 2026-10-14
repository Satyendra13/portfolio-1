from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Backend API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "secret-key-for-dev-environment-12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./asistline.db"
    DATABASE_URL_SYNC: str = "sqlite:///./asistline.db"

    # LiveKit WebRTC
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # AI Models (Gemini & ElevenLabs)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_ID: str = "gemini-2.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 3072

    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_STT_MODEL: str = "scribe_v2_realtime"
    ELEVENLABS_TTS_MODEL: str = "eleven_multilingual_v2"

    # Operational thresholds
    DEFAULT_KB_MIN_SCORE: float = 0.45
    DEFAULT_QUEUE_TIMEOUT_SECONDS: int = 45
    DEFAULT_SILENCE_TIMEOUT_SECONDS: float = 6.0

    # Mock Backends URL
    MOCK_BACKENDS_URL: str = "http://localhost:9000"

    model_config = {
        "env_file": str(ENV_FILE_PATH),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
