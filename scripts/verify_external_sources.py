"""Contrôler les sources CSV et JSON externes."""

import json
from pathlib import Path

import polars as pl

ROOT_DIRECTORY = Path(__file__).resolve().parents[1]

RETURNS_DIRECTORY = ROOT_DIRECTORY / "source_data" / "returns"

INVENTORY_DIRECTORY = ROOT_DIRECTORY / "source_data" / "inventory"

DELIVERY_FILE = ROOT_DIRECTORY / "source_data" / "deliveries" / "delivery_events.json"


def verify_returns() -> None:
    """Contrôler les fichiers de retours."""

    files = sorted(RETURNS_DIRECTORY.glob("returns_*.csv"))

    if not files:
        raise RuntimeError("Aucun fichier de retours.")

    data = pl.concat([pl.read_csv(file) for file in files])

    required_columns = {
        "return_id",
        "order_id",
        "order_item_id",
        "product_id",
        "returned_quantity",
        "return_reason",
        "return_status",
        "return_date",
        "refund_amount",
    }

    if not required_columns.issubset(set(data.columns)):
        raise RuntimeError("Colonnes de retours manquantes.")

    invalid_quantities = data.filter(pl.col("returned_quantity") <= 0).height

    if invalid_quantities != 0:
        raise RuntimeError("Quantités de retour invalides.")

    duplicated_returns = data.group_by("return_id").len().filter(pl.col("len") > 1).height

    if duplicated_returns != 0:
        raise RuntimeError("return_id dupliqué.")

    print(f"[OK] retours : {len(files)} fichiers / {data.height:,} lignes")


def verify_inventory() -> None:
    """Contrôler les snapshots d'inventaire."""

    files = sorted(INVENTORY_DIRECTORY.glob("inventory_*.csv"))

    if not files:
        raise RuntimeError("Aucun fichier d'inventaire.")

    data = pl.concat([pl.read_csv(file) for file in files])

    negative_stock = data.filter(
        (pl.col("available_quantity") < 0)
        | (pl.col("reserved_quantity") < 0)
        | (pl.col("damaged_quantity") < 0)
    ).height

    if negative_stock != 0:
        raise RuntimeError("Stock négatif détecté.")

    duplicate_rows = (
        data.group_by(
            [
                "snapshot_date",
                "store_id",
                "product_id",
            ]
        )
        .len()
        .filter(pl.col("len") > 1)
        .height
    )

    if duplicate_rows != 0:
        raise RuntimeError("Snapshots dupliqués.")

    print(f"[OK] inventaire : {len(files)} fichiers / {data.height:,} lignes")


def verify_deliveries() -> None:
    """Contrôler les événements logistiques."""

    if not DELIVERY_FILE.exists():
        raise RuntimeError("delivery_events.json absent.")

    events = json.loads(DELIVERY_FILE.read_text(encoding="utf-8"))

    if not events:
        raise RuntimeError("Aucun événement de livraison.")

    required_fields = {
        "delivery_id",
        "order_id",
        "carrier",
        "delivery_status",
        "event_timestamp",
        "shipping_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "destination_city",
    }

    for event in events:
        if not required_fields.issubset(event):
            raise RuntimeError("Événement logistique invalide.")

    print(f"[OK] livraisons : {len(events):,} événements")


def main() -> None:
    """Exécuter tous les contrôles."""

    verify_returns()
    verify_inventory()
    verify_deliveries()

    print("Toutes les sources externes sont valides.")


if __name__ == "__main__":
    main()
