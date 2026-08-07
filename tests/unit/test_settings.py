"""Tests de la configuration RetailPulse 360."""

from ingestion.common.settings import get_settings


def test_environment_is_loaded() -> None:
    """Vérifier le chargement de l'environnement."""

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.environment == "development"


def test_postgres_configuration() -> None:
    """Vérifier la configuration PostgreSQL."""

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.postgres_database == "retailpulse"
    assert settings.postgres_port > 0
    assert isinstance(settings.postgres_port, int)


def test_minio_configuration() -> None:
    """Vérifier la configuration MinIO."""

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.minio_bucket == "retailpulse-raw"
    assert settings.minio_endpoint == "localhost:9000"
