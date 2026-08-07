"""Configuration du générateur de données source."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class GenerationConfig:
    """Paramètres utilisés pour produire un dataset reproductible."""

    customer_count: int = 2_000
    product_count: int = 250
    store_count: int = 12
    order_count: int = 10_000
    seed: int = 42
    start_date: datetime = datetime(2025, 1, 1, tzinfo=UTC)
    end_date: datetime = field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0))

    def validate(self) -> None:
        """Valider les paramètres avant de générer les données."""

        counts = {
            "customer_count": self.customer_count,
            "product_count": self.product_count,
            "store_count": self.store_count,
            "order_count": self.order_count,
        }

        for name, value in counts.items():
            if value <= 0:
                raise ValueError(f"{name} doit être strictement positif.")

        if self.start_date >= self.end_date:
            raise ValueError("start_date doit être antérieure à end_date.")
