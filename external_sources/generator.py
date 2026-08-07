"""Génération des fichiers CSV et événements logistiques."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import polars as pl
from sqlalchemy import Engine, text

from external_sources.config import ExternalSourcesConfig

RETURN_REASONS = [
    "DAMAGED_PRODUCT",
    "WRONG_PRODUCT",
    "CUSTOMER_CHANGED_MIND",
    "SIZE_OR_COMPATIBILITY",
    "DELIVERY_DELAY",
    "OTHER",
]

CARRIERS = [
    "Atlas Express",
    "Maghreb Delivery",
    "Rapid Maroc",
    "Orient Express",
]


def money(value: Decimal | float | int) -> Decimal:
    """Arrondir un montant à deux décimales."""

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


class ExternalSourceGenerator:
    """Produire les sources externes de RetailPulse."""

    def __init__(
        self,
        engine: Engine,
        config: ExternalSourcesConfig,
    ) -> None:
        config.validate()

        self.engine = engine
        self.config = config
        self.random = random.Random(config.seed)

    def _query(
        self,
        sql: str,
    ) -> list[dict[str, Any]]:
        """Exécuter une requête et retourner des dictionnaires."""

        with self.engine.connect() as connection:
            rows = connection.execute(text(sql)).mappings().all()

        return [dict(row) for row in rows]

    def generate_returns(
        self,
        output_directory: Path,
    ) -> int:
        """Générer les fichiers journaliers de retours."""

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        rows = self._query(
            """
            SELECT
                orders.order_id,
                orders.order_status,
                orders.order_date,
                items.order_item_id,
                items.product_id,
                items.quantity,
                items.unit_price,
                items.discount_percentage
            FROM source.orders AS orders
            INNER JOIN source.order_items AS items
                ON items.order_id = orders.order_id
            WHERE orders.order_status IN (
                'DELIVERED',
                'REFUNDED'
            )
              AND orders.order_date >=
                  NOW() - INTERVAL '60 days'
            ORDER BY
                orders.order_id,
                items.order_item_id
            """
        )

        today = datetime.now(UTC).date()

        generated: list[dict[str, Any]] = []

        return_number = 1

        for row in rows:
            must_return = row["order_status"] == "REFUNDED"

            selected = must_return or self.random.random() < self.config.return_rate

            if not selected:
                continue

            order_date = row["order_date"].date()

            earliest_return = order_date + timedelta(days=1)

            latest_return = min(
                order_date + timedelta(days=30),
                today,
            )

            if earliest_return > latest_return:
                continue

            available_days = (latest_return - earliest_return).days

            return_date = earliest_return + timedelta(
                days=self.random.randint(
                    0,
                    max(available_days, 0),
                )
            )

            returned_quantity = self.random.randint(
                1,
                int(row["quantity"]),
            )

            paid_unit_price = Decimal(str(row["unit_price"])) * (
                Decimal("1") - Decimal(str(row["discount_percentage"]))
            )

            refund_amount = money(paid_unit_price * returned_quantity)

            return_status = self.random.choices(
                [
                    "APPROVED",
                    "REFUNDED",
                    "REJECTED",
                ],
                weights=[20, 75, 5],
                k=1,
            )[0]

            generated.append(
                {
                    "return_id": (f"RET-{return_number:08d}"),
                    "order_id": row["order_id"],
                    "order_item_id": (row["order_item_id"]),
                    "product_id": row["product_id"],
                    "returned_quantity": (returned_quantity),
                    "return_reason": (self.random.choice(RETURN_REASONS)),
                    "return_status": (return_status),
                    "return_date": (return_date.isoformat()),
                    "refund_amount": float(refund_amount),
                }
            )

            return_number += 1

        grouped: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for row in generated:
            grouped[row["return_date"]].append(row)

        for return_date, daily_rows in grouped.items():
            filename = output_directory / f"returns_{return_date.replace('-', '_')}.csv"

            pl.DataFrame(daily_rows).write_csv(filename)

        return len(generated)

    def generate_inventory(
        self,
        output_directory: Path,
    ) -> int:
        """Créer des snapshots quotidiens d'inventaire."""

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stores = self._query(
            """
            SELECT
                store_id
            FROM source.stores
            WHERE active = TRUE
            ORDER BY store_id
            """
        )

        products = self._query(
            """
            SELECT
                product_id
            FROM source.products
            WHERE active = TRUE
            ORDER BY product_id
            """
        )

        end_date = datetime.now(UTC).date()

        start_date = end_date - timedelta(days=self.config.inventory_days - 1)

        stock_state: dict[
            tuple[str, str],
            int,
        ] = {}

        reorder_thresholds: dict[
            tuple[str, str],
            int,
        ] = {}

        for store in stores:
            for product in products:
                key = (
                    store["store_id"],
                    product["product_id"],
                )

                stock_state[key] = self.random.randint(
                    10,
                    120,
                )

                reorder_thresholds[key] = self.random.randint(
                    8,
                    25,
                )

        total_rows = 0

        for day_offset in range(self.config.inventory_days):
            snapshot_date = start_date + timedelta(days=day_offset)

            rows: list[dict[str, Any]] = []

            for store in stores:
                for product in products:
                    key = (
                        store["store_id"],
                        product["product_id"],
                    )

                    current_stock = stock_state[key]

                    sold_or_moved = self.random.randint(
                        0,
                        8,
                    )

                    current_stock = max(
                        0,
                        current_stock - sold_or_moved,
                    )

                    if current_stock <= reorder_thresholds[key] and self.random.random() < 0.35:
                        current_stock += self.random.randint(
                            20,
                            80,
                        )

                    reserved_quantity = self.random.randint(
                        0,
                        min(
                            current_stock,
                            8,
                        ),
                    )

                    damaged_quantity = self.random.choices(
                        [0, 1, 2],
                        weights=[92, 6, 2],
                        k=1,
                    )[0]

                    available_quantity = max(
                        0,
                        current_stock - reserved_quantity - damaged_quantity,
                    )

                    stock_state[key] = current_stock

                    rows.append(
                        {
                            "snapshot_date": (snapshot_date.isoformat()),
                            "store_id": (store["store_id"]),
                            "product_id": (product["product_id"]),
                            "available_quantity": (available_quantity),
                            "reserved_quantity": (reserved_quantity),
                            "damaged_quantity": (damaged_quantity),
                            "reorder_threshold": (reorder_thresholds[key]),
                        }
                    )

            filename = output_directory / (
                "inventory_" + snapshot_date.strftime("%Y_%m_%d") + ".csv"
            )

            pl.DataFrame(rows).write_csv(filename)

            total_rows += len(rows)

        return total_rows

    def generate_deliveries(
        self,
        output_file: Path,
    ) -> int:
        """Créer l'historique d'événements de livraison."""

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        history_days = self.config.delivery_history_days

        orders = self._query(
            f"""
            SELECT
                orders.order_id,
                orders.order_status,
                orders.order_date,
                customers.city AS customer_city
            FROM source.orders AS orders
            INNER JOIN source.customers AS customers
                ON customers.customer_id =
                   orders.customer_id
            WHERE orders.order_status IN (
                'SHIPPED',
                'DELIVERED',
                'REFUNDED'
            )
              AND orders.order_date >=
                  NOW() - INTERVAL '{history_days} days'
            ORDER BY orders.order_date
            """
        )

        events: list[dict[str, Any]] = []

        delivery_number = 1

        for order in orders:
            delivery_id = f"DEL-{delivery_number:09d}"

            carrier = self.random.choice(CARRIERS)

            order_datetime = order["order_date"]

            shipping_datetime = order_datetime + timedelta(
                hours=self.random.randint(
                    6,
                    30,
                )
            )

            expected_date = order_datetime.date() + timedelta(
                days=self.random.randint(
                    3,
                    7,
                )
            )

            delay_days = self.random.choices(
                [-1, 0, 1, 2, 3],
                weights=[10, 55, 20, 10, 5],
                k=1,
            )[0]

            actual_date = expected_date + timedelta(days=delay_days)

            sequence: list[tuple[str, datetime]] = [
                (
                    "CREATED",
                    order_datetime + timedelta(hours=1),
                ),
                (
                    "PICKED_UP",
                    shipping_datetime,
                ),
                (
                    "IN_TRANSIT",
                    shipping_datetime
                    + timedelta(
                        hours=self.random.randint(
                            8,
                            30,
                        )
                    ),
                ),
            ]

            if order["order_status"] in {
                "DELIVERED",
                "REFUNDED",
            }:
                out_for_delivery = datetime.combine(
                    actual_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                ) + timedelta(hours=8)

                delivered_at = out_for_delivery + timedelta(
                    hours=self.random.randint(
                        2,
                        10,
                    )
                )

                sequence.extend(
                    [
                        (
                            "OUT_FOR_DELIVERY",
                            out_for_delivery,
                        ),
                        (
                            "DELIVERED",
                            delivered_at,
                        ),
                    ]
                )

                actual_delivery_date: str | None = actual_date.isoformat()

            else:
                actual_delivery_date = None

            for status, event_timestamp in sequence:
                events.append(
                    {
                        "delivery_id": delivery_id,
                        "order_id": (order["order_id"]),
                        "carrier": carrier,
                        "delivery_status": status,
                        "event_timestamp": (
                            event_timestamp.astimezone(UTC)
                            .isoformat()
                            .replace(
                                "+00:00",
                                "Z",
                            )
                        ),
                        "shipping_date": (shipping_datetime.date().isoformat()),
                        "expected_delivery_date": (expected_date.isoformat()),
                        "actual_delivery_date": (actual_delivery_date),
                        "destination_city": (order["customer_city"]),
                    }
                )

            delivery_number += 1

        events.sort(key=lambda row: row["event_timestamp"])

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                events,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return len(events)
