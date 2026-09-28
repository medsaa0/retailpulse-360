"""Comparer les volumes de lignes entre RAW et les marts finaux (ANALYTICS)."""

from __future__ import annotations

import sys

from snowflake_load.client import get_connection

# (table_raw, table_mart, colonne_de_comptage_dans_le_mart)
RECONCILIATION_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("RAW.ORDERS_RAW", "ANALYTICS.FCT_ORDERS", "order_id"),
    ("RAW.CUSTOMERS_RAW", "ANALYTICS.DIM_CUSTOMER", "customer_id"),
    ("RAW.PRODUCTS_RAW", "ANALYTICS.DIM_PRODUCT", "product_id"),
)


def count_distinct(connection, table: str, column: str) -> int:
    """Compter les valeurs distinctes d'une colonne dans une table Snowflake."""

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(DISTINCT {column}) FROM {table}")
        return cursor.fetchone()[0]


def main() -> None:
    connection = get_connection()
    has_anomaly = False

    try:
        print("Réconciliation RAW -> ANALYTICS")
        print("-" * 50)

        for raw_table, mart_table, key_column in RECONCILIATION_CHECKS:
            raw_count = count_distinct(connection, raw_table, key_column)
            mart_count = count_distinct(connection, mart_table, key_column)

            status = "OK" if mart_count > 0 else "ANOMALIE"
            if mart_count == 0 and raw_count > 0:
                has_anomaly = True

            print(
                f"{raw_table:<28} {raw_count:>8} | "
                f"{mart_table:<24} {mart_count:>8} | {status}"
            )

    finally:
        connection.close()

    print("-" * 50)

    if has_anomaly:
        print("Réconciliation ÉCHOUÉE : des marts sont vides alors que RAW a des données.")
        sys.exit(1)

    print("Réconciliation OK.")


if __name__ == "__main__":
    main()