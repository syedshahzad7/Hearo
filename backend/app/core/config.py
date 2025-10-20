from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: C:\Hearo
PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # DB
    DATABASE_URL: str

    # Env
    HEARO_ENV: str = "dev"

    # JWT/Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60         # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7            # 7 days

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


