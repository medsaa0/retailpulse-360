"""Tests du cadrage et des contrats de données."""

from pathlib import Path

import yaml

ROOT_DIRECTORY = Path(__file__).resolve().parents[2]


def load_yaml(relative_path: str) -> dict:
    """Charger un fichier YAML depuis la racine du projet."""

    file_path = ROOT_DIRECTORY / relative_path

    with file_path.open(encoding="utf-8-sig") as yaml_file:
        content = yaml.safe_load(yaml_file)

    assert isinstance(content, dict)

    return content


def test_business_documents_exist() -> None:
    """Vérifier que les documents métier sont présents."""

    expected_documents = [
        "docs/01_contexte_metier.md",
        "docs/02_sources_donnees.md",
        "docs/03_kpis_regles_metier.md",
        "docs/architecture/modele_dimensionnel.md",
        "docs/decisions/ADR-001-architecture-elt.md",
    ]

    for relative_path in expected_documents:
        assert (ROOT_DIRECTORY / relative_path).exists(), f"Document manquant : {relative_path}"


def test_project_configuration_exists() -> None:
    """Vérifier les paramètres généraux du projet."""

    configuration = load_yaml("configs/project.yml")

    assert configuration["project"]["name"] == "retailpulse-360"
    assert configuration["project"]["country"] == "Morocco"
    assert configuration["project"]["analytics_currency"] == "MAD"
    assert configuration["warehouse"]["platform"] == "snowflake"
    assert configuration["storage"]["local_platform"] == "minio"
    assert configuration["orchestration"]["platform"] == "airflow"
    assert configuration["transformation"]["platform"] == "dbt-core"


def test_required_sources_are_declared() -> None:
    """Vérifier la présence des quatre sources principales."""

    configuration = load_yaml("configs/project.yml")

    source_names = {source["name"] for source in configuration["sources"]}

    expected_sources = {
        "transactional_database",
        "returns_files",
        "inventory_files",
        "delivery_api",
    }

    assert source_names == expected_sources


def test_expected_datasets_are_declared() -> None:
    """Vérifier la présence de tous les datasets."""

    contracts = load_yaml("contracts/source_contracts.yml")

    dataset_names = {dataset["name"] for dataset in contracts["datasets"]}

    expected_datasets = {
        "customers",
        "products",
        "stores",
        "orders",
        "order_items",
        "returns",
        "inventory",
        "deliveries",
    }

    assert dataset_names == expected_datasets


def test_all_datasets_have_primary_keys() -> None:
    """Vérifier que chaque dataset possède une clé primaire."""

    contracts = load_yaml("contracts/source_contracts.yml")

    for dataset in contracts["datasets"]:
        assert dataset["primary_key"], f"Clé primaire absente pour {dataset['name']}."


def test_all_datasets_have_columns() -> None:
    """Vérifier que chaque dataset possède des colonnes."""

    contracts = load_yaml("contracts/source_contracts.yml")

    for dataset in contracts["datasets"]:
        assert dataset["columns"], f"Aucune colonne déclarée pour {dataset['name']}."


def test_every_dataset_has_a_load_strategy() -> None:
    """Vérifier la stratégie de chargement de chaque dataset."""

    contracts = load_yaml("contracts/source_contracts.yml")

    allowed_strategies = {
        "incremental",
        "append",
        "full",
    }

    for dataset in contracts["datasets"]:
        assert dataset["load_strategy"] in allowed_strategies


def test_sensitive_customer_columns_are_identified() -> None:
    """Vérifier l'identification des données personnelles."""

    contracts = load_yaml("contracts/source_contracts.yml")

    customers_contract = next(
        dataset for dataset in contracts["datasets"] if dataset["name"] == "customers"
    )

    sensitive_columns = {
        column["name"] for column in customers_contract["columns"] if column.get("sensitive", False)
    }

    assert sensitive_columns == {
        "first_name",
        "last_name",
        "email",
        "phone",
    }


def test_primary_key_columns_exist_in_datasets() -> None:
    """Vérifier que les clés primaires existent parmi les colonnes."""

    contracts = load_yaml("contracts/source_contracts.yml")

    for dataset in contracts["datasets"]:
        column_names = {column["name"] for column in dataset["columns"]}

        for primary_key_column in dataset["primary_key"]:
            assert primary_key_column in column_names, (
                f"La clé {primary_key_column} est absente des colonnes de {dataset['name']}."
            )


def test_non_nullable_primary_keys() -> None:
    """Vérifier que les clés primaires ne sont pas nullables."""

    contracts = load_yaml("contracts/source_contracts.yml")

    for dataset in contracts["datasets"]:
        columns_by_name = {column["name"]: column for column in dataset["columns"]}

        for primary_key_column in dataset["primary_key"]:
            assert columns_by_name[primary_key_column]["nullable"] is False, (
                f"La clé {primary_key_column} de {dataset['name']} ne peut pas être nullable."
            )
