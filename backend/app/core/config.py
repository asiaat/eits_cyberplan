import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

import os

_env_candidates = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    ".env",
]
_env_file = next((f for f in _env_candidates if os.path.exists(f)), ".env")


class Settings(BaseSettings):
    APP_ENV: str = Field(default="local", validation_alias="APP_ENV")
    APP_NAME: str = Field(default="eits-management-system", validation_alias="APP_NAME")

    POSTGRES_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="eits", validation_alias="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="eits", validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="eits_dev_password", validation_alias="POSTGRES_PASSWORD")

    DATABASE_URL: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")

    REDIS_URL: str = Field(default="redis://redis:6379/0", validation_alias="REDIS_URL")

    MINIO_ENDPOINT: str = Field(default="minio:9000", validation_alias="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="eits-evidence", validation_alias="MINIO_BUCKET")
    MINIO_SECURE: bool = Field(default=False, validation_alias="MINIO_SECURE")

    JWT_SECRET_KEY: str = Field(default="change-me-in-local-only", validation_alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="BACKEND_CORS_ORIGINS"
    )

    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()