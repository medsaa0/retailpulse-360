"""Chargement des données générées dans PostgreSQL."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

from sqlalchemy import (
    URL,
    Connection,
    Engine,
    create_engine,
    text,
)
from sqlalchemy.exc import OperationalError

from ingestion.common.settings import get_settings

TABLE_LOAD_ORDER = [
    "stores",
    "customers",
    "products",
    "orders",
    "order_items",
]


def create_postgres_engine() -> Engine:
    """Créer un moteur SQLAlchemy PostgreSQL."""

    settings = get_settings()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_database,
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        hide_parameters=True,
    )


def wait_for_database(
    engine: Engine,
    attempts: int = 30,
    delay_seconds: float = 2.0,
) -> None:
    """Attendre que PostgreSQL accepte les connexions."""

    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return

        except OperationalError as error:
            if attempt == attempts:
                raise RuntimeError(
                    "PostgreSQL n'est pas disponible après plusieurs tentatives."
                ) from error

            time.sleep(delay_seconds)


def _chunks(
    rows: list[dict[str, Any]],
    chunk_size: int,
) -> Iterable[list[dict[str, Any]]]:
    """Découper une liste en lots."""

    for start_index in range(
        0,
        len(rows),
        chunk_size,
    ):
        yield rows[start_index : start_index + chunk_size]


def _reset_source_tables(
    connection: Connection,
) -> None:
    """Vider les tables source."""

    connection.execute(
        text(
            """
            TRUNCATE TABLE
                source.order_items,
                source.orders,
                source.customers,
                source.products,
                source.stores
            CASCADE
            """
        )
    )


def _insert_rows(
    connection: Connection,
    table_name: str,
    rows: list[dict[str, Any]],
    chunk_size: int = 1_000,
) -> None:
    """Insérer les lignes en lots."""

    if table_name not in TABLE_LOAD_ORDER:
        raise ValueError(f"Table non autorisée : {table_name}")

    if not rows:
        return

    columns = list(rows[0])
    column_sql = ", ".join(columns)

    parameter_sql = ", ".join(f":{column}" for column in columns)

    statement = text(f"INSERT INTO source.{table_name} ({column_sql}) VALUES ({parameter_sql})")

    for batch in _chunks(
        rows,
        chunk_size,
    ):
        connection.execute(
            statement,
            batch,
        )


def load_generated_data(
    engine: Engine,
    datasets: dict[str, list[dict[str, Any]]],
    reset: bool = True,
) -> None:
    """Charger les datasets dans une transaction."""

    with engine.begin() as connection:
        if reset:
            _reset_source_tables(connection)

        for table_name in TABLE_LOAD_ORDER:
            _insert_rows(
                connection,
                table_name,
                datasets[table_name],
            )


def count_rows(
    engine: Engine,
) -> dict[str, int]:
    """Compter les lignes des tables source."""

    counts: dict[str, int] = {}

    with engine.connect() as connection:
        for table_name in TABLE_LOAD_ORDER:
            value = connection.execute(
                text(f"SELECT COUNT(*) FROM source.{table_name}")
            ).scalar_one()

            counts[table_name] = int(value)

    return counts
