from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root path of the entire project
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # --- API ---
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # --- Database ---
    DATABASE_URL: str

    # --- Environment ---
    HEARO_ENV: str = "dev"

    # --- JWT / Auth ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 days

    # --- File uploads ---
    UPLOAD_DIR: str = str(PROJECT_ROOT / "uploads")

    # --- NEW (Phase 9): transcription options ---
    WHISPER_MODEL: str = "base"        # tiny | base | small | medium
    WHISPER_DEVICE: str = "cpu"        # "cpu" on Windows; use "cuda" if you have CUDA
    WHISPER_COMPUTE_TYPE: str = "int8" # safe default for CPU: int8

    # --- Config ---
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
