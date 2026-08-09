"""Pipeline d'ingestion vers la RAW Zone MinIO."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import polars as pl

from ingestion.api.client import fetch_delivery_events
from ingestion.common.hashing import sha256_file
from ingestion.common.parquet import (
    dataframe_to_parquet_bytes,
)
from ingestion.common.state import (
    load_state,
    save_state,
)
from ingestion.common.storage import ObjectStorage
from ingestion.postgres.extractor import (
    SOURCE_TABLES,
    extract_table,
)

ROOT_DIRECTORY = Path(__file__).resolve().parents[1]

RETURNS_DIRECTORY = ROOT_DIRECTORY / "source_data" / "returns"

INVENTORY_DIRECTORY = ROOT_DIRECTORY / "source_data" / "inventory"


def utc_now() -> datetime:
    """Retourner maintenant en UTC."""

    return datetime.now(UTC).replace(microsecond=0)


def iso_utc(
    value: datetime,
) -> str:
    """Convertir une date UTC en chaîne ISO."""

    return (
        value.astimezone(UTC)
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def parse_iso(
    value: str | None,
) -> datetime | None:
    """Convertir une chaîne ISO en datetime."""

    if value is None:
        return None

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def timestamp_token(
    value: datetime,
) -> str:
    """Créer une valeur utilisable dans une clé S3."""

    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def source_date_from_filename(
    file_path: Path,
) -> str:
    """Extraire YYYY-MM-DD depuis un nom de fichier."""

    parts = file_path.stem.split("_")

    if len(parts) < 4:
        raise ValueError(f"Nom de fichier invalide : {file_path.name}")

    return "-".join(parts[-3:])


def upload_dataframe(
    storage: ObjectStorage,
    dataframe: pl.DataFrame,
    object_key: str,
    metadata: dict[str, str],
) -> None:
    """Convertir en Parquet puis envoyer vers MinIO."""

    parquet_data = dataframe_to_parquet_bytes(dataframe)

    storage.put_bytes(
        key=object_key,
        data=parquet_data,
        content_type=("application/vnd.apache.parquet"),
        metadata=metadata,
    )


def ingest_postgresql(
    storage: ObjectStorage,
    state: dict[str, Any],
    manifest_entries: list[dict[str, Any]],
    ingestion_date: str,
) -> None:
    """Ingestion incrémentale PostgreSQL."""

    watermarks = state["postgres_watermarks"]

    for table_name in SOURCE_TABLES:
        previous_value = watermarks.get(table_name)

        previous_watermark = parse_iso(previous_value)

        dataframe, new_watermark = extract_table(
            table_name,
            previous_watermark,
        )

        if dataframe.is_empty():
            manifest_entries.append(
                {
                    "source": "postgresql",
                    "dataset": table_name,
                    "status": "SKIPPED",
                    "rows": 0,
                    "reason": "NO_NEW_ROWS",
                }
            )

            continue

        if new_watermark is None:
            raise RuntimeError(f"Watermark absent pour {table_name}.")

        new_watermark_iso = iso_utc(new_watermark)

        token = timestamp_token(new_watermark)

        object_key = (
            f"postgresql/{table_name}/"
            f"ingestion_date={ingestion_date}/"
            f"watermark_to={token}/"
            "data.parquet"
        )

        upload_dataframe(
            storage=storage,
            dataframe=dataframe,
            object_key=object_key,
            metadata={
                "source": "postgresql",
                "dataset": table_name,
                "row-count": str(dataframe.height),
                "watermark-to": token,
            },
        )

        watermarks[table_name] = new_watermark_iso

        manifest_entries.append(
            {
                "source": "postgresql",
                "dataset": table_name,
                "status": "LOADED",
                "rows": dataframe.height,
                "object_key": object_key,
                "watermark_from": (previous_value),
                "watermark_to": (new_watermark_iso),
            }
        )


def ingest_csv_directory(
    storage: ObjectStorage,
    state: dict[str, Any],
    manifest_entries: list[dict[str, Any]],
    dataset_name: str,
    directory: Path,
) -> None:
    """Ingestion idempotente d'un dossier CSV."""

    processed_files = state["processed_files"]

    for file_path in sorted(directory.glob("*.csv")):
        relative_path = file_path.relative_to(ROOT_DIRECTORY).as_posix()

        checksum = sha256_file(file_path)

        if processed_files.get(relative_path) == checksum:
            manifest_entries.append(
                {
                    "source": "csv",
                    "dataset": dataset_name,
                    "status": "SKIPPED",
                    "file": relative_path,
                    "reason": "ALREADY_PROCESSED",
                }
            )

            continue

        dataframe = pl.read_csv(
            file_path,
            try_parse_dates=True,
        )

        if dataframe.is_empty():
            manifest_entries.append(
                {
                    "source": "csv",
                    "dataset": dataset_name,
                    "status": "SKIPPED",
                    "file": relative_path,
                    "reason": "EMPTY_FILE",
                }
            )

            processed_files[relative_path] = checksum

            continue

        source_date = source_date_from_filename(file_path)

        object_key = (
            f"csv/{dataset_name}/"
            f"source_date={source_date}/"
            f"{file_path.stem}__"
            f"{checksum[:12]}.parquet"
        )

        upload_dataframe(
            storage=storage,
            dataframe=dataframe,
            object_key=object_key,
            metadata={
                "source": "csv",
                "dataset": dataset_name,
                "source-file": (file_path.name),
                "sha256": checksum,
                "row-count": str(dataframe.height),
            },
        )

        processed_files[relative_path] = checksum

        manifest_entries.append(
            {
                "source": "csv",
                "dataset": dataset_name,
                "status": "LOADED",
                "rows": dataframe.height,
                "file": relative_path,
                "sha256": checksum,
                "object_key": object_key,
            }
        )


def ingest_delivery_api(
    storage: ObjectStorage,
    state: dict[str, Any],
    manifest_entries: list[dict[str, Any]],
    ingestion_date: str,
) -> None:
    """Ingestion incrémentale de l'API."""

    previous_value = state.get("delivery_watermark")

    previous_watermark = parse_iso(previous_value)

    events = fetch_delivery_events(previous_watermark)

    if not events:
        manifest_entries.append(
            {
                "source": "api",
                "dataset": "deliveries",
                "status": "SKIPPED",
                "rows": 0,
                "reason": "NO_NEW_EVENTS",
            }
        )

        return

    event_times = [parse_iso(event["event_timestamp"]) for event in events]

    valid_event_times = [value for value in event_times if value is not None]

    if not valid_event_times:
        raise RuntimeError("Aucun event_timestamp valide.")

    new_watermark = max(valid_event_times)

    dataframe = pl.DataFrame(
        events,
        infer_schema_length=None,
    )

    new_watermark_iso = iso_utc(new_watermark)

    token = timestamp_token(new_watermark)

    object_key = (
        f"api/deliveries/ingestion_date={ingestion_date}/watermark_to={token}/events.parquet"
    )

    upload_dataframe(
        storage=storage,
        dataframe=dataframe,
        object_key=object_key,
        metadata={
            "source": "api",
            "dataset": "deliveries",
            "row-count": str(dataframe.height),
            "watermark-to": token,
        },
    )

    state["delivery_watermark"] = new_watermark_iso

    manifest_entries.append(
        {
            "source": "api",
            "dataset": "deliveries",
            "status": "LOADED",
            "rows": dataframe.height,
            "object_key": object_key,
            "watermark_from": previous_value,
            "watermark_to": (new_watermark_iso),
        }
    )


def main() -> None:
    """Exécuter un run complet d'ingestion."""

    started_at = utc_now()

    run_id = str(uuid4())

    ingestion_date = started_at.date().isoformat()

    print(f"Début ingestion | run_id={run_id}")

    storage = ObjectStorage()

    storage.ensure_bucket()

    original_state = load_state(storage)

    new_state = deepcopy(original_state)

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "started_at": iso_utc(started_at),
        "status": "RUNNING",
        "datasets": [],
    }

    manifest_entries = manifest["datasets"]

    try:
        print("1/3 PostgreSQL -> MinIO...")

        ingest_postgresql(
            storage=storage,
            state=new_state,
            manifest_entries=manifest_entries,
            ingestion_date=ingestion_date,
        )

        print("2/3 CSV -> MinIO...")

        ingest_csv_directory(
            storage=storage,
            state=new_state,
            manifest_entries=manifest_entries,
            dataset_name="returns",
            directory=RETURNS_DIRECTORY,
        )

        ingest_csv_directory(
            storage=storage,
            state=new_state,
            manifest_entries=manifest_entries,
            dataset_name="inventory",
            directory=INVENTORY_DIRECTORY,
        )

        print("3/3 API -> MinIO...")

        ingest_delivery_api(
            storage=storage,
            state=new_state,
            manifest_entries=manifest_entries,
            ingestion_date=ingestion_date,
        )

        save_state(
            storage,
            new_state,
        )

        manifest["status"] = "SUCCESS"

        print("Ingestion terminée avec succès.")

    except Exception as error:
        manifest["status"] = "FAILED"

        manifest["error"] = f"{type(error).__name__}: {error}"

        raise

    finally:
        finished_at = utc_now()

        manifest["finished_at"] = iso_utc(finished_at)

        manifest_key = f"_audit/manifests/ingestion_date={ingestion_date}/run_id={run_id}.json"

        storage.put_json(
            manifest_key,
            manifest,
        )


if __name__ == "__main__":
    main()
