"""Tests des composants génériques d'ingestion."""

import polars as pl

from ingestion.common.hashing import sha256_file
from ingestion.common.parquet import (
    dataframe_to_parquet_bytes,
    parquet_bytes_to_dataframe,
)
from ingestion.common.state import default_state


def test_parquet_round_trip() -> None:
    """Vérifier l'écriture et lecture Parquet."""

    original = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": [
                "a",
                "b",
                "c",
            ],
        }
    )

    content = dataframe_to_parquet_bytes(original)

    restored = parquet_bytes_to_dataframe(content)

    assert restored.equals(original)


def test_sha256_is_reproducible(
    tmp_path,
) -> None:
    """Vérifier la stabilité du checksum."""

    file_path = tmp_path / "sample.csv"

    file_path.write_text(
        "id,value\n1,test\n",
        encoding="utf-8",
    )

    first_checksum = sha256_file(file_path)

    second_checksum = sha256_file(file_path)

    assert first_checksum == second_checksum

    assert len(first_checksum) == 64


def test_default_state() -> None:
    """Vérifier la structure du premier état."""

    state = default_state()

    assert state["postgres_watermarks"] == {}

    assert state["delivery_watermark"] is None

    assert state["processed_files"] == {}
