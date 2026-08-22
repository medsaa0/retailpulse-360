"""Chargement des objets RAW MinIO vers Snowflake."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from snowflake.connector import DictCursor
from snowflake.connector.connection import SnowflakeConnection

from ingestion.common.storage import ObjectStorage
from snowflake_load.client import get_connection
from snowflake_load.mapping import resolve_target_table

STAGE_NAME = "RETAILPULSE.RAW.INGEST_STAGE"

FILE_FORMAT_NAME = (
    "RETAILPULSE.RAW.PARQUET_FORMAT"
)


def utc_now() -> datetime:
    """Retourner l'heure UTC actuelle."""

    return datetime.now(UTC).replace(
        microsecond=0
    )


def successful_object_keys(
    connection: SnowflakeConnection,
) -> set[str]:
    """Retourner les objets MinIO déjà chargés."""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT DISTINCT MINIO_OBJECT_KEY
            FROM RETAILPULSE.AUDIT.FILE_LOADS
            WHERE STATUS = 'SUCCESS'
            """
        )

        return {
            str(row[0])
            for row in cursor.fetchall()
        }

    finally:
        cursor.close()


def discover_objects(
    storage: ObjectStorage,
) -> list[str]:
    """Lister les Parquet reconnus dans MinIO."""

    objects: list[str] = []

    for object_key in storage.list_keys():
        if not object_key.endswith(
            ".parquet"
        ):
            continue

        if resolve_target_table(
            object_key
        ) is None:
            continue

        objects.append(
            object_key
        )

    return sorted(objects)


def download_object(
    storage: ObjectStorage,
    object_key: str,
    temporary_root: Path,
) -> Path:
    """Télécharger un objet MinIO dans un dossier temporaire."""

    relative_path = PurePosixPath(
        object_key
    )

    local_path = temporary_root.joinpath(
        *relative_path.parts
    )

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    local_path.write_bytes(
        storage.get_bytes(
            object_key
        )
    )

    return local_path


def stage_location(
    object_key: str,
) -> tuple[str, str]:
    """Retourner le chemin de stage et le nom du fichier."""

    path = PurePosixPath(
        object_key
    )

    parent = path.parent.as_posix()

    stage_directory = (
        f"@{STAGE_NAME}/{parent}/"
    )

    return (
        stage_directory,
        path.name,
    )


def dictionary_value(
    row: dict[str, Any],
    name: str,
) -> Any:
    """Lire une colonne d'un DictCursor sans dépendre de la casse."""

    return (
        row.get(name)
        or row.get(name.lower())
        or row.get(name.upper())
    )


def audit_file_load(
    connection: SnowflakeConnection,
    *,
    run_id: str,
    object_key: str,
    stage_file: str | None,
    target_table: str,
    rows_parsed: int,
    rows_loaded: int,
    status: str,
    copy_query_id: str | None,
    error_message: str | None,
) -> None:
    """Enregistrer le résultat d'un fichier."""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO RETAILPULSE.AUDIT.FILE_LOADS (
                LOAD_ID,
                RUN_ID,
                MINIO_OBJECT_KEY,
                STAGE_FILE,
                TARGET_TABLE,
                ROWS_PARSED,
                ROWS_LOADED,
                STATUS,
                COPY_QUERY_ID,
                ERROR_MESSAGE,
                LOADED_AT
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP()
            )
            """,
            (
                str(uuid4()),
                run_id,
                object_key,
                stage_file,
                target_table,
                rows_parsed,
                rows_loaded,
                status,
                copy_query_id,
                error_message,
            ),
        )

    finally:
        cursor.close()


def start_run(
    connection: SnowflakeConnection,
    run_id: str,
    objects_found: int,
) -> None:
    """Créer l'entrée d'audit du run."""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO RETAILPULSE.AUDIT.LOAD_RUNS (
                RUN_ID,
                STARTED_AT,
                STATUS,
                OBJECTS_FOUND
            )
            VALUES (
                %s,
                CURRENT_TIMESTAMP(),
                'RUNNING',
                %s
            )
            """,
            (
                run_id,
                objects_found,
            ),
        )

    finally:
        cursor.close()


def finish_run(
    connection: SnowflakeConnection,
    *,
    run_id: str,
    status: str,
    objects_loaded: int,
    rows_loaded: int,
    error_message: str | None = None,
) -> None:
    """Terminer l'entrée d'audit du run."""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE RETAILPULSE.AUDIT.LOAD_RUNS
            SET
                FINISHED_AT = CURRENT_TIMESTAMP(),
                STATUS = %s,
                OBJECTS_LOADED = %s,
                ROWS_LOADED = %s,
                ERROR_MESSAGE = %s
            WHERE RUN_ID = %s
            """,
            (
                status,
                objects_loaded,
                rows_loaded,
                error_message,
                run_id,
            ),
        )

    finally:
        cursor.close()


def load_one_object(
    *,
    connection: SnowflakeConnection,
    storage: ObjectStorage,
    run_id: str,
    object_key: str,
    temporary_root: Path,
) -> int:
    """Charger un objet MinIO dans sa table RAW."""

    target_table = resolve_target_table(
        object_key
    )

    if target_table is None:
        raise ValueError(
            f"Aucune table pour {object_key}"
        )

    local_path = download_object(
        storage,
        object_key,
        temporary_root,
    )

    stage_directory, filename = (
        stage_location(
            object_key
        )
    )

    stage_file = (
        f"{stage_directory}{filename}"
    )

    local_uri = (
        local_path.resolve().as_uri()
    )

    put_cursor = connection.cursor()

    try:
        put_cursor.execute(
            f"""
            PUT {local_uri}
            {stage_directory}
            AUTO_COMPRESS = FALSE
            OVERWRITE = TRUE
            PARALLEL = 4
            """
        )

    finally:
        put_cursor.close()

    copy_cursor = connection.cursor(
        DictCursor
    )

    try:
        copy_cursor.execute(
            f"""
            COPY INTO {target_table}
            FROM {stage_directory}
            FILES = ('{filename}')
            FILE_FORMAT = (
                FORMAT_NAME =
                '{FILE_FORMAT_NAME}'
            )
            MATCH_BY_COLUMN_NAME =
                CASE_INSENSITIVE
            INCLUDE_METADATA = (
                LOAD_FILENAME =
                    METADATA$FILENAME,
                LOAD_FILE_ROW_NUMBER =
                    METADATA$FILE_ROW_NUMBER,
                LOAD_TS =
                    METADATA$START_SCAN_TIME
            )
            ON_ERROR = ABORT_STATEMENT
            PURGE = TRUE
            """
        )

        results = copy_cursor.fetchall()

        rows_parsed = sum(
            int(
                dictionary_value(
                    row,
                    "ROWS_PARSED",
                )
                or 0
            )
            for row in results
        )

        rows_loaded = sum(
            int(
                dictionary_value(
                    row,
                    "ROWS_LOADED",
                )
                or 0
            )
            for row in results
        )

        query_id = copy_cursor.sfqid

    except Exception as error:
        query_id = copy_cursor.sfqid

        audit_file_load(
            connection,
            run_id=run_id,
            object_key=object_key,
            stage_file=stage_file,
            target_table=target_table,
            rows_parsed=0,
            rows_loaded=0,
            status="FAILED",
            copy_query_id=query_id,
            error_message=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )

        raise

    finally:
        copy_cursor.close()

    audit_file_load(
        connection,
        run_id=run_id,
        object_key=object_key,
        stage_file=stage_file,
        target_table=target_table,
        rows_parsed=rows_parsed,
        rows_loaded=rows_loaded,
        status="SUCCESS",
        copy_query_id=query_id,
        error_message=None,
    )

    return rows_loaded


def run_load() -> None:
    """Charger tous les nouveaux objets RAW."""

    run_id = str(
        uuid4()
    )

    print(
        f"Début Snowflake load | run_id={run_id}"
    )

    storage = ObjectStorage()
    storage.ensure_bucket()

    connection = get_connection()

    discovered_objects = discover_objects(
        storage
    )

    already_loaded = successful_object_keys(
        connection
    )

    pending_objects = [
        object_key
        for object_key in discovered_objects
        if object_key not in already_loaded
    ]

    print(
        f"Objets MinIO trouvés : "
        f"{len(discovered_objects)}"
    )

    print(
        f"Déjà chargés : "
        f"{len(already_loaded)}"
    )

    print(
        f"À charger : "
        f"{len(pending_objects)}"
    )

    start_run(
        connection,
        run_id,
        len(discovered_objects),
    )

    loaded_object_count = 0
    total_rows_loaded = 0

    try:
        with tempfile.TemporaryDirectory(
            prefix="retailpulse_snowflake_"
        ) as temporary_directory:
            temporary_root = Path(
                temporary_directory
            )

            for position, object_key in enumerate(
                pending_objects,
                start=1,
            ):
                table_name = resolve_target_table(
                    object_key
                )

                print(
                    f"[{position}/"
                    f"{len(pending_objects)}] "
                    f"{object_key} "
                    f"-> {table_name}"
                )

                rows_loaded = load_one_object(
                    connection=connection,
                    storage=storage,
                    run_id=run_id,
                    object_key=object_key,
                    temporary_root=temporary_root,
                )

                loaded_object_count += 1
                total_rows_loaded += (
                    rows_loaded
                )

                print(
                    f"   {rows_loaded:,} "
                    "lignes chargées."
                )

        finish_run(
            connection,
            run_id=run_id,
            status="SUCCESS",
            objects_loaded=loaded_object_count,
            rows_loaded=total_rows_loaded,
        )

        print(
            "Chargement Snowflake terminé."
        )

        print(
            f"Objets chargés : "
            f"{loaded_object_count}"
        )

        print(
            f"Lignes chargées : "
            f"{total_rows_loaded:,}"
        )

    except Exception as error:
        finish_run(
            connection,
            run_id=run_id,
            status="FAILED",
            objects_loaded=loaded_object_count,
            rows_loaded=total_rows_loaded,
            error_message=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )

        raise

    finally:
        connection.close()
