"""DAG principal RetailPulse 360 : ingestion -> Snowflake -> dbt -> réconciliation."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/dbt_retailpulse"

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


def check_sources_reachable() -> None:
    """Vérifier que PostgreSQL et l'API de livraison répondent avant d'extraire."""

    import os
    import sys

    import psycopg
    import requests

    postgres_dsn = (
        f"host={os.environ['POSTGRES_HOST']} "
        f"port={os.environ['POSTGRES_PORT']} "
        f"dbname={os.environ['POSTGRES_DATABASE']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )

    try:
        with psycopg.connect(postgres_dsn, connect_timeout=5) as conn:
            conn.execute("SELECT 1")
    except Exception as error:  # noqa: BLE001
        print(f"PostgreSQL injoignable: {error}", file=sys.stderr)
        raise

    delivery_url = os.environ["DELIVERY_API_BASE_URL"] + "/health"

    try:
        response = requests.get(delivery_url, timeout=5)
        response.raise_for_status()
    except Exception as error:  # noqa: BLE001
        print(f"API livraison injoignable: {error}", file=sys.stderr)
        raise

    print("Toutes les sources sont accessibles.")


with DAG(
    dag_id="retailpulse_elt_pipeline",
    description="Pipeline ELT complet : sources -> MinIO -> Snowflake -> dbt",
    default_args=default_args,
    schedule="0 3 * * *",          # tous les jours à 3h du matin (UTC)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["retailpulse", "elt"],
) as dag:

    check_sources = PythonOperator(
        task_id="check_sources",
        python_callable=check_sources_reachable,
    )

    extract_and_upload_to_minio = BashOperator(
        task_id="extract_and_upload_to_minio",
        bash_command=f"cd {PROJECT_DIR} && python -m ingestion.run_ingestion",
    )

    load_snowflake_raw = BashOperator(
        task_id="load_snowflake_raw",
        bash_command=f"cd {PROJECT_DIR} && python -m scripts.load_raw_to_snowflake",
    )

    dbt_snapshot = BashOperator(
    task_id="dbt_snapshot",
    bash_command=f"cd {DBT_DIR} && dbt snapshot --profiles-dir /opt/airflow/project/dbt_profiles",
    )

    dbt_run_staging = BashOperator(
    task_id="dbt_run_staging",
    bash_command=(
              f"cd {DBT_DIR} && "
              "dbt run --select staging "
              "--profiles-dir /opt/airflow/project/dbt_profiles"
              ),
    )

    dbt_run_marts = BashOperator(
    task_id="dbt_run_marts",
    bash_command=(
       f"cd {DBT_DIR} && "
       "dbt run --select marts "
       "--profiles-dir /opt/airflow/project/dbt_profiles"
       ),
    )

    dbt_test = BashOperator(
    task_id="dbt_test",
    bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir /opt/airflow/project/dbt_profiles",
    )
    record_data_quality = BashOperator(
    task_id="record_data_quality",
    bash_command=f"cd {PROJECT_DIR} && python -m scripts.record_data_quality",
    )

    reconcile_counts = BashOperator(
        task_id="reconcile_counts",
        bash_command=f"cd {PROJECT_DIR} && python -m scripts.reconcile_counts",
    )

    pipeline_success = EmptyOperator(task_id="pipeline_success")


    (
    check_sources
    >> extract_and_upload_to_minio
    >> load_snowflake_raw
    >> dbt_run_staging
    >> dbt_snapshot
    >> dbt_run_marts
    >> dbt_test
    >> record_data_quality
    >> reconcile_counts
    >> pipeline_success
    )