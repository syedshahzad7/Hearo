# backend/app/core/config.py
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: C:\Hearo
PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    DATABASE_URL: str                      # required
    HEARO_ENV: str = "dev"                 # <-- add this so it’s recognized

    # pydantic v2 style config
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",                    # <-- ignore any other extra keys later
    )



