"""Extraction incrémentale depuis PostgreSQL."""

from __future__ import annotations

from datetime import datetime

import polars as pl
from sqlalchemy import URL, create_engine, text

from ingestion.common.settings import get_settings

SOURCE_TABLES = (
    "customers",
    "products",
    "stores",
    "orders",
    "order_items",
)


def extract_table(
    table_name: str,
    watermark: datetime | None,
) -> tuple[
    pl.DataFrame,
    datetime | None,
]:
    """Extraire une table depuis le dernier watermark."""

    if table_name not in SOURCE_TABLES:
        raise ValueError(f"Table non autorisée : {table_name}")

    settings = get_settings()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_database,
    )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        hide_parameters=True,
    )

    if watermark is None:
        query = text(
            f"""
            SELECT *
            FROM source.{table_name}
            ORDER BY updated_at
            """
        )

        parameters = {}

    else:
        query = text(
            f"""
            SELECT *
            FROM source.{table_name}
            WHERE updated_at > :watermark
            ORDER BY updated_at
            """
        )

        parameters = {
            "watermark": watermark,
        }

    with engine.connect() as connection:
        rows = (
            connection.execute(
                query,
                parameters,
            )
            .mappings()
            .all()
        )

    if not rows:
        return (
            pl.DataFrame(),
            watermark,
        )

    records = [dict(row) for row in rows]

    new_watermark = max(row["updated_at"] for row in records)

    dataframe = pl.DataFrame(
        records,
        infer_schema_length=None,
    )

    return (
        dataframe,
        new_watermark,
    )
