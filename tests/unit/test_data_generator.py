"""Tests du générateur de données source."""

from datetime import UTC, datetime

from data_generator.config import GenerationConfig
from data_generator.generator import RetailDataGenerator


def generate_small_dataset() -> dict:
    """Créer un petit dataset pour les tests."""

    configuration = GenerationConfig(
        customer_count=30,
        product_count=20,
        store_count=5,
        order_count=50,
        seed=123,
        start_date=datetime(
            2025,
            1,
            1,
            tzinfo=UTC,
        ),
        end_date=datetime(
            2026,
            8,
            6,
            tzinfo=UTC,
        ),
    )

    return RetailDataGenerator(configuration).generate_all()


def test_generated_table_counts() -> None:
    """Vérifier les volumes configurés."""

    datasets = generate_small_dataset()

    assert len(datasets["customers"]) == 30
    assert len(datasets["products"]) == 20
    assert len(datasets["stores"]) == 5
    assert len(datasets["orders"]) == 50
    assert len(datasets["order_items"]) >= 50


def test_orders_reference_existing_entities() -> None:
    """Vérifier les clients et magasins."""

    datasets = generate_small_dataset()

    customer_ids = {row["customer_id"] for row in datasets["customers"]}

    store_ids = {row["store_id"] for row in datasets["stores"]}

    for order in datasets["orders"]:
        assert order["customer_id"] in customer_ids

        if order["channel"] == "STORE":
            assert order["store_id"] in store_ids
        else:
            assert order["store_id"] is None


def test_order_items_reference_orders_and_products() -> None:
    """Vérifier les relations des articles."""

    datasets = generate_small_dataset()

    order_ids = {row["order_id"] for row in datasets["orders"]}

    product_ids = {row["product_id"] for row in datasets["products"]}

    for item in datasets["order_items"]:
        assert item["order_id"] in order_ids

        assert item["product_id"] in product_ids


def test_order_item_business_rules() -> None:
    """Vérifier les règles métier."""

    datasets = generate_small_dataset()

    for item in datasets["order_items"]:
        assert item["quantity"] > 0
        assert item["unit_price"] >= 0
        assert item["unit_cost"] >= 0

        assert 0 <= item["discount_percentage"] <= 1


def test_order_item_keys_are_unique() -> None:
    """Vérifier l'unicité des articles."""

    datasets = generate_small_dataset()

    business_keys = [
        (
            row["order_id"],
            row["order_item_id"],
        )
        for row in datasets["order_items"]
    ]

    assert len(business_keys) == len(set(business_keys))


def test_generation_is_reproducible_with_same_seed() -> None:
    """Vérifier la reproductibilité."""

    first_dataset = generate_small_dataset()
    second_dataset = generate_small_dataset()

    first_customer_ids = [row["customer_id"] for row in first_dataset["customers"]]

    second_customer_ids = [row["customer_id"] for row in second_dataset["customers"]]

    assert first_customer_ids == second_customer_ids
