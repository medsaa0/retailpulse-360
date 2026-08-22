"""Mapping entre les objets MinIO et les tables Snowflake RAW."""

from __future__ import annotations

OBJECT_TABLE_MAPPING = (
    (
        "postgresql/customers/",
        "RAW.CUSTOMERS_RAW",
    ),
    (
        "postgresql/products/",
        "RAW.PRODUCTS_RAW",
    ),
    (
        "postgresql/stores/",
        "RAW.STORES_RAW",
    ),
    (
        "postgresql/orders/",
        "RAW.ORDERS_RAW",
    ),
    (
        "postgresql/order_items/",
        "RAW.ORDER_ITEMS_RAW",
    ),
    (
        "csv/returns/",
        "RAW.RETURNS_RAW",
    ),
    (
        "csv/inventory/",
        "RAW.INVENTORY_RAW",
    ),
    (
        "api/deliveries/",
        "RAW.DELIVERIES_RAW",
    ),
)


def resolve_target_table(
    object_key: str,
) -> str | None:
    """Trouver la table Snowflake correspondant à une clé MinIO."""

    for prefix, table_name in OBJECT_TABLE_MAPPING:
        if object_key.startswith(prefix):
            return table_name

    return None
