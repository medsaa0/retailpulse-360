"""Génération de données retail cohérentes et reproductibles."""

from __future__ import annotations

import random
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from faker import Faker

from data_generator.config import GenerationConfig

MOROCCAN_LOCATIONS = [
    ("Casablanca", "Casablanca-Settat"),
    ("Rabat", "Rabat-Salé-Kénitra"),
    ("Marrakech", "Marrakech-Safi"),
    ("Tanger", "Tanger-Tétouan-Al Hoceïma"),
    ("Oujda", "Oriental"),
    ("Fès", "Fès-Meknès"),
    ("Agadir", "Souss-Massa"),
    ("Meknès", "Fès-Meknès"),
    ("Kénitra", "Rabat-Salé-Kénitra"),
    ("Tétouan", "Tanger-Tétouan-Al Hoceïma"),
    ("El Jadida", "Casablanca-Settat"),
    ("Nador", "Oriental"),
]

PRODUCT_CATALOG = {
    "Électronique": {
        "subcategories": [
            "Smartphone",
            "Tablette",
            "Casque",
            "Montre connectée",
        ],
        "brands": [
            "AtlasTech",
            "Nova",
            "Sahara Digital",
            "Maghreb One",
        ],
        "price_range": (249, 8_999),
    },
    "Informatique": {
        "subcategories": [
            "Ordinateur portable",
            "Clavier",
            "Souris",
            "Écran",
        ],
        "brands": [
            "AtlasTech",
            "DataPro",
            "Nova",
            "PixelWorks",
        ],
        "price_range": (99, 14_999),
    },
    "Électroménager": {
        "subcategories": [
            "Mixeur",
            "Aspirateur",
            "Machine à café",
            "Four",
        ],
        "brands": [
            "MaisonPlus",
            "Rif Home",
            "Atlas Home",
            "Nova",
        ],
        "price_range": (199, 6_999),
    },
    "Maison": {
        "subcategories": [
            "Lampe",
            "Chaise",
            "Table",
            "Rangement",
        ],
        "brands": [
            "MaisonPlus",
            "Rif Home",
            "Casa Design",
            "Atlas Home",
        ],
        "price_range": (49, 3_499),
    },
    "Sport": {
        "subcategories": [
            "Chaussures",
            "Tapis fitness",
            "Ballon",
            "Sac de sport",
        ],
        "brands": [
            "ActiveMA",
            "Atlas Sport",
            "RifFit",
            "UrbanMove",
        ],
        "price_range": (59, 1_999),
    },
    "Beauté": {
        "subcategories": [
            "Soin visage",
            "Parfum",
            "Sèche-cheveux",
            "Tondeuse",
        ],
        "brands": [
            "ArganCare",
            "Rose Atlas",
            "Nour",
            "Casa Beauty",
        ],
        "price_range": (39, 1_499),
    },
    "Mode": {
        "subcategories": [
            "Veste",
            "Pantalon",
            "Chemise",
            "Sac",
        ],
        "brands": [
            "Medina Style",
            "UrbanMA",
            "Atlas Wear",
            "Rif Collection",
        ],
        "price_range": (79, 1_799),
    },
}

CHANNELS = [
    "WEB",
    "MOBILE",
    "STORE",
    "CALL_CENTER",
]

PAYMENT_METHODS = {
    "WEB": [
        "CARD",
        "MOBILE_WALLET",
        "CASH_ON_DELIVERY",
    ],
    "MOBILE": [
        "CARD",
        "MOBILE_WALLET",
        "CASH_ON_DELIVERY",
    ],
    "STORE": [
        "CARD",
        "CASH",
        "MOBILE_WALLET",
    ],
    "CALL_CENTER": [
        "CASH_ON_DELIVERY",
        "CARD",
    ],
}


def _money(value: float | Decimal) -> Decimal:
    """Arrondir une valeur monétaire à deux décimales."""

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _slugify(value: str) -> str:
    """Transformer un texte pour construire une adresse email."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")

    return re.sub(
        r"[^a-z0-9]+",
        ".",
        ascii_value.lower(),
    ).strip(".")


class RetailDataGenerator:
    """Produire les tables source PostgreSQL du projet."""

    def __init__(self, config: GenerationConfig) -> None:
        config.validate()

        self.config = config
        self.random = random.Random(config.seed)
        self.fake = Faker("fr_FR")
        self.fake.seed_instance(config.seed)

    def _random_datetime(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> datetime:
        """Générer une date UTC dans un intervalle."""

        lower_bound = start or self.config.start_date
        upper_bound = end or self.config.end_date

        total_seconds = int((upper_bound - lower_bound).total_seconds())

        offset = self.random.randint(
            0,
            max(total_seconds, 0),
        )

        return lower_bound + timedelta(seconds=offset)

    def generate_stores(self) -> list[dict[str, Any]]:
        """Créer les magasins physiques."""

        stores: list[dict[str, Any]] = []

        for index in range(self.config.store_count):
            city, region = MOROCCAN_LOCATIONS[index % len(MOROCCAN_LOCATIONS)]

            created_at = self._random_datetime(
                datetime(2018, 1, 1, tzinfo=UTC),
                datetime(2024, 12, 31, tzinfo=UTC),
            )

            stores.append(
                {
                    "store_id": f"STR-{index + 1:03d}",
                    "store_name": f"RetailPulse {city}",
                    "city": city,
                    "region": region,
                    "opening_date": created_at.date(),
                    "active": self.random.random() > 0.03,
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            )

        return stores

    def generate_customers(
        self,
    ) -> list[dict[str, Any]]:
        """Créer les clients."""

        customers: list[dict[str, Any]] = []

        for index in range(self.config.customer_count):
            customer_id = f"CUS-{index + 1:07d}"
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            city, _ = self.random.choice(MOROCCAN_LOCATIONS)

            created_at = self._random_datetime()

            maximum_update = min(
                created_at + timedelta(days=self.random.randint(0, 180)),
                self.config.end_date,
            )

            updated_at = self._random_datetime(
                created_at,
                maximum_update,
            )

            email_prefix = f"{_slugify(first_name)}.{_slugify(last_name)}"

            phone_suffix = self.random.randint(
                10_000_000,
                99_999_999,
            )

            customers.append(
                {
                    "customer_id": customer_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": (f"{email_prefix}.{index + 1}@example.ma"),
                    "phone": f"+2126{phone_suffix}",
                    "city": city,
                    "country": "Morocco",
                    "customer_segment": (
                        self.random.choices(
                            [
                                "STANDARD",
                                "PREMIUM",
                                "VIP",
                            ],
                            weights=[75, 20, 5],
                            k=1,
                        )[0]
                    ),
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )

        return customers

    def generate_products(
        self,
    ) -> list[dict[str, Any]]:
        """Créer un catalogue multi-catégories."""

        products: list[dict[str, Any]] = []
        categories = list(PRODUCT_CATALOG)

        for index in range(self.config.product_count):
            category = categories[index % len(categories)]

            details = PRODUCT_CATALOG[category]

            subcategory = self.random.choice(details["subcategories"])

            brand = self.random.choice(details["brands"])

            minimum_price, maximum_price = details["price_range"]

            unit_price = _money(
                self.random.uniform(
                    minimum_price,
                    maximum_price,
                )
            )

            cost_ratio = Decimal(
                str(
                    self.random.uniform(
                        0.52,
                        0.78,
                    )
                )
            )

            unit_cost = _money(unit_price * cost_ratio)

            created_at = self._random_datetime(
                datetime(2023, 1, 1, tzinfo=UTC),
                self.config.end_date,
            )

            maximum_update = min(
                created_at + timedelta(days=self.random.randint(0, 120)),
                self.config.end_date,
            )

            products.append(
                {
                    "product_id": (f"PRD-{index + 1:06d}"),
                    "product_name": (f"{subcategory} {brand} M{index + 1:04d}"),
                    "category": category,
                    "subcategory": subcategory,
                    "brand": brand,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                    "active": (self.random.random() > 0.04),
                    "created_at": created_at,
                    "updated_at": (
                        self._random_datetime(
                            created_at,
                            maximum_update,
                        )
                    ),
                }
            )

        return products

    def _status_for_order(
        self,
        order_date: datetime,
    ) -> str:
        """Choisir un statut selon l'ancienneté."""

        order_age_days = (self.config.end_date - order_date).days

        if order_age_days <= 3:
            statuses = [
                "CREATED",
                "PAID",
                "PROCESSING",
                "SHIPPED",
                "CANCELLED",
            ]
            weights = [20, 25, 30, 20, 5]

        elif order_age_days <= 10:
            statuses = [
                "PROCESSING",
                "SHIPPED",
                "DELIVERED",
                "CANCELLED",
            ]
            weights = [10, 35, 50, 5]

        else:
            statuses = [
                "DELIVERED",
                "CANCELLED",
                "REFUNDED",
            ]
            weights = [88, 7, 5]

        return self.random.choices(
            statuses,
            weights=weights,
            k=1,
        )[0]

    def generate_orders(
        self,
        customers: list[dict[str, Any]],
        stores: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Créer les commandes."""

        customer_ids = [row["customer_id"] for row in customers]

        store_ids = [row["store_id"] for row in stores if row["active"]]

        orders: list[dict[str, Any]] = []

        for index in range(self.config.order_count):
            order_id = f"ORD-{index + 1:09d}"
            order_date = self._random_datetime()

            channel = self.random.choices(
                CHANNELS,
                weights=[42, 28, 22, 8],
                k=1,
            )[0]

            store_id = self.random.choice(store_ids) if channel == "STORE" else None

            status = self._status_for_order(order_date)

            maximum_update = min(
                order_date + timedelta(days=self.random.randint(0, 14)),
                self.config.end_date,
            )

            orders.append(
                {
                    "order_id": order_id,
                    "customer_id": (self.random.choice(customer_ids)),
                    "store_id": store_id,
                    "channel": channel,
                    "order_status": status,
                    "order_date": order_date,
                    "currency": "MAD",
                    "payment_method": (self.random.choice(PAYMENT_METHODS[channel])),
                    "created_at": order_date,
                    "updated_at": (
                        self._random_datetime(
                            order_date,
                            maximum_update,
                        )
                    ),
                }
            )

        return orders

    def generate_order_items(
        self,
        orders: list[dict[str, Any]],
        products: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Créer un à cinq articles par commande."""

        order_items: list[dict[str, Any]] = []

        for order in orders:
            item_count = self.random.randint(
                1,
                min(5, len(products)),
            )

            selected_products = self.random.sample(
                products,
                item_count,
            )

            for position, product in enumerate(
                selected_products,
                start=1,
            ):
                list_price = product["unit_price"]

                price_factor = Decimal(
                    str(
                        self.random.uniform(
                            0.97,
                            1.03,
                        )
                    )
                )

                unit_price = _money(list_price * price_factor)

                discount_percentage = self.random.choices(
                    [
                        Decimal("0.00"),
                        Decimal("0.05"),
                        Decimal("0.10"),
                        Decimal("0.15"),
                        Decimal("0.20"),
                    ],
                    weights=[55, 15, 15, 10, 5],
                    k=1,
                )[0]

                order_items.append(
                    {
                        "order_item_id": (f"{order['order_id']}-ITEM-{position:02d}"),
                        "order_id": order["order_id"],
                        "product_id": (product["product_id"]),
                        "quantity": (
                            self.random.choices(
                                [1, 2, 3, 4],
                                weights=[68, 22, 8, 2],
                                k=1,
                            )[0]
                        ),
                        "unit_price": unit_price,
                        "unit_cost": (product["unit_cost"]),
                        "discount_percentage": (discount_percentage),
                        "created_at": (order["created_at"]),
                        "updated_at": (order["updated_at"]),
                    }
                )

        return order_items

    def generate_all(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        """Créer toutes les tables PostgreSQL."""

        stores = self.generate_stores()
        customers = self.generate_customers()
        products = self.generate_products()

        orders = self.generate_orders(
            customers,
            stores,
        )

        order_items = self.generate_order_items(
            orders,
            products,
        )

        return {
            "stores": stores,
            "customers": customers,
            "products": products,
            "orders": orders,
            "order_items": order_items,
        }
