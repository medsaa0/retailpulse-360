"""Vérifier la qualité de la base source PostgreSQL."""

from sqlalchemy import text

from data_generator.loader import (
    count_rows,
    create_postgres_engine,
    wait_for_database,
)

QUALITY_CHECKS = {
    "commandes sans client": """
        SELECT COUNT(*)
        FROM source.orders AS orders
        LEFT JOIN source.customers AS customers
            ON customers.customer_id =
               orders.customer_id
        WHERE customers.customer_id IS NULL
    """,
    "articles sans commande": """
        SELECT COUNT(*)
        FROM source.order_items AS items
        LEFT JOIN source.orders AS orders
            ON orders.order_id =
               items.order_id
        WHERE orders.order_id IS NULL
    """,
    "articles sans produit": """
        SELECT COUNT(*)
        FROM source.order_items AS items
        LEFT JOIN source.products AS products
            ON products.product_id =
               items.product_id
        WHERE products.product_id IS NULL
    """,
    "quantités invalides": """
        SELECT COUNT(*)
        FROM source.order_items
        WHERE quantity <= 0
    """,
    "réductions invalides": """
        SELECT COUNT(*)
        FROM source.order_items
        WHERE discount_percentage < 0
           OR discount_percentage > 1
    """,
    "devises invalides": """
        SELECT COUNT(*)
        FROM source.orders
        WHERE currency <> 'MAD'
    """,
    "commandes futures": """
        SELECT COUNT(*)
        FROM source.orders
        WHERE order_date > NOW()
    """,
    "clés article dupliquées": """
        SELECT COUNT(*)
        FROM (
            SELECT
                order_id,
                order_item_id
            FROM source.order_items
            GROUP BY
                order_id,
                order_item_id
            HAVING COUNT(*) > 1
        ) AS duplicates
    """,
}


def main() -> None:
    """Exécuter tous les contrôles."""

    engine = create_postgres_engine()
    wait_for_database(engine)

    counts = count_rows(engine)

    print("Volumes des tables :")

    for table_name, row_count in counts.items():
        print(f"  source.{table_name}: {row_count:,}")

    failures: list[str] = []

    with engine.connect() as connection:
        for check_name, query in QUALITY_CHECKS.items():
            result = int(connection.execute(text(query)).scalar_one())

            status = "OK" if result == 0 else "ERREUR"

            print(f"[{status}] {check_name}: {result}")

            if result != 0:
                failures.append(f"{check_name}: {result}")

    empty_tables = [table_name for table_name, row_count in counts.items() if row_count == 0]

    if empty_tables:
        failures.append("Tables vides : " + ", ".join(empty_tables))

    if failures:
        raise SystemExit("Contrôles échoués :\n- " + "\n- ".join(failures))

    print("Tous les contrôles PostgreSQL sont valides.")


if __name__ == "__main__":
    main()
