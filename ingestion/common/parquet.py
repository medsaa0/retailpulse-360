"""Fonctions utilitaires pour Apache Parquet."""

from io import BytesIO

import polars as pl


def dataframe_to_parquet_bytes(
    dataframe: pl.DataFrame,
) -> bytes:
    """Convertir un DataFrame Polars en Parquet."""

    buffer = BytesIO()

    dataframe.write_parquet(
        buffer,
        compression="zstd",
        statistics=True,
    )

    return buffer.getvalue()


def parquet_bytes_to_dataframe(
    data: bytes,
) -> pl.DataFrame:
    """Lire un fichier Parquet contenu en mémoire."""

    return pl.read_parquet(BytesIO(data))
