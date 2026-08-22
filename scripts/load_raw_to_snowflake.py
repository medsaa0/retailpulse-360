"""Charger la RAW Zone MinIO dans Snowflake."""

from snowflake_load.loader import run_load


def main() -> None:
    """Exécuter le chargement."""

    run_load()


if __name__ == "__main__":
    main()
