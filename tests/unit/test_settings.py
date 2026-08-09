"""Tests de la configuration RetailPulse 360."""

from ingestion.common.settings import get_settings


def test_environment_is_loaded() -> None:
    """Vérifier le chargement de l'environnement."""

    get_settings.cache_clear()

    settings = get_settings()

    assert settings.environment == "development"


def test_postgres_configuration() -> None:
    """Vérifier PostgreSQL."""

    get_settings.cache_clear()

    settings = get_settings()

    assert settings.postgres_database == "retailpulse"

    assert isinstance(
        settings.postgres_port,
        int,
    )

    assert settings.postgres_port > 0


def test_minio_configuration() -> None:
    """Vérifier MinIO."""

    get_settings.cache_clear()

    settings = get_settings()

    assert settings.minio_bucket == "retailpulse-raw"

    assert settings.minio_endpoint.startswith("http")


def test_delivery_api_configuration() -> None:
    """Vérifier l'URL de l'API."""

    get_settings.cache_clear()

    settings = get_settings()

    assert settings.delivery_api_base_url == "http://127.0.0.1:8002"
