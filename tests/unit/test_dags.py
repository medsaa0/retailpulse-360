"""Vérifier que les DAGs Airflow sont syntaxiquement valides."""

from __future__ import annotations

import pytest

pytest.importorskip("airflow")

from airflow.models import DagBag  # noqa: E402


def test_dags_have_no_import_errors() -> None:
    """Aucun DAG ne doit avoir d'erreur d'import."""

    dag_bag = DagBag(dag_folder="airflow/dags", include_examples=False)

    assert dag_bag.import_errors == {}, dag_bag.import_errors


def test_elt_pipeline_dag_exists() -> None:
    """Le DAG principal doit être chargé avec au moins 8 tâches."""

    dag_bag = DagBag(dag_folder="airflow/dags", include_examples=False)
    dag = dag_bag.get_dag("retailpulse_elt_pipeline")

    assert dag is not None
    assert len(dag.tasks) >= 8