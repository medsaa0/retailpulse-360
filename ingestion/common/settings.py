"""Configuration centrale du projet RetailPulse 360."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables chargées depuis le fichier .env."""

    environment: str = "development"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "retailpulse"
    postgres_user: str = "retailpulse"
    postgres_password: str = "retailpulse"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "retailpulse-raw"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Retourner une instance unique de la configuration."""

    return Settings()
