"""Configuration centrale du projet RetailPulse 360."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables chargées depuis le fichier .env."""

    environment: str = "development"

    postgres_host: str = "localhost"
    postgres_port: int = 5434
    postgres_database: str = "retailpulse"
    postgres_user: str = "retailpulse"
    postgres_password: str = "retailpulse"

    minio_endpoint: str = "http://127.0.0.1:9002"
    minio_access_key: str = "retailpulse"
    minio_secret_key: str = "retailpulse_minio_password"
    minio_bucket: str = "retailpulse-raw"

    delivery_api_base_url: str = "http://127.0.0.1:8002"

    snowflake_account: str = "NZGYBYT-LF06500"
    snowflake_user: str = "MOHAS0"
    snowflake_password: str = "Mohammedsa1010@"
    snowflake_authenticator: str = "snowflake"
    snowflake_role: str = "SYSADMIN"
    snowflake_warehouse: str = "RETAILPULSE_WH"
    snowflake_database: str = "RETAILPULSE"
    snowflake_schema: str = "RAW"

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
