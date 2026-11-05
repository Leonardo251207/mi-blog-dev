"""Configuración tipada por entorno."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    app_mode: str = "minimal"
    app_port: int = 8000

    storage: str = "auto"
    mongo_uri: str = ""
    mongo_db: str = "metrics"

    admin_api_key: str = "dev-admin-key"
    ip_hash_salt: str = "dev-salt-change-me"

    cors_origins: str = "http://localhost:8000"
    cors_origin_regex: str = r"https://.*\.vercel\.app"

    bootstrap_file: str = "config/bootstrap.yaml"
    bootstrap_on_start: bool = True

    dev_beacon_key: str = "pk_live_dev_00000000000000000000000000000000"
    beacon_rate_limit_per_minute: int = 600

    @property
    def cors_origins_list(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]

    @property
    def es_local(self) -> bool:
        return self.app_env in {"local", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
