"""Vérification de la RAW Zone MinIO."""

from ingestion.common.parquet import (
    parquet_bytes_to_dataframe,
)
from ingestion.common.state import (
    STATE_KEY,
)
from ingestion.common.storage import (
    ObjectStorage,
)

EXPECTED_PREFIXES = [
    "postgresql/customers/",
    "postgresql/products/",
    "postgresql/stores/",
    "postgresql/orders/",
    "postgresql/order_items/",
    "csv/returns/",
    "csv/inventory/",
    "api/deliveries/",
    "_audit/manifests/",
]


def main() -> None:
    """Contrôler la RAW Zone."""

    storage = ObjectStorage()

    storage.ensure_bucket()

    all_keys = storage.list_keys()

    print(f"Bucket : {storage.bucket}")

    print(f"Nombre d'objets : {len(all_keys)}")

    failures: list[str] = []

    for prefix in EXPECTED_PREFIXES:
        matching_keys = [key for key in all_keys if key.startswith(prefix)]

        if not matching_keys:
            failures.append(f"Préfixe absent : {prefix}")

            print(f"[ERREUR] {prefix}")

            continue

        print(f"[OK] {prefix} ({len(matching_keys)} objets)")

        parquet_keys = [key for key in matching_keys if key.endswith(".parquet")]

        if parquet_keys:
            sample_key = parquet_keys[0]

            dataframe = parquet_bytes_to_dataframe(storage.get_bytes(sample_key))

            if dataframe.is_empty():
                failures.append(f"Parquet vide : {sample_key}")

    state = storage.get_json(
        STATE_KEY,
        {},
    )

    if not state:
        failures.append("État d'ingestion absent.")

    else:
        print("[OK] ingestion_state.json")

        postgres_watermarks = state.get(
            "postgres_watermarks",
            {},
        )

        for table_name in [
            "customers",
            "products",
            "stores",
            "orders",
            "order_items",
        ]:
            if not postgres_watermarks.get(table_name):
                failures.append(f"Watermark absent : {table_name}")

        if not state.get("delivery_watermark"):
            failures.append("Watermark API absent.")

    if failures:
        raise SystemExit("Contrôles RAW échoués :\n- " + "\n- ".join(failures))

    print("RAW Data Lake valide.")


if __name__ == "__main__":
    main()
