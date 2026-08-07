"""Générer les fichiers CSV et événements API."""

from pathlib import Path

from data_generator.loader import (
    create_postgres_engine,
    wait_for_database,
)
from external_sources.config import (
    ExternalSourcesConfig,
)
from external_sources.generator import (
    ExternalSourceGenerator,
)

ROOT_DIRECTORY = Path(__file__).resolve().parents[1]

RETURNS_DIRECTORY = ROOT_DIRECTORY / "source_data" / "returns"

INVENTORY_DIRECTORY = ROOT_DIRECTORY / "source_data" / "inventory"

DELIVERY_FILE = ROOT_DIRECTORY / "source_data" / "deliveries" / "delivery_events.json"


def main() -> None:
    """Créer toutes les sources externes."""

    print("1/5 Connexion à PostgreSQL...")

    engine = create_postgres_engine()
    wait_for_database(engine)

    configuration = ExternalSourcesConfig(
        seed=42,
        return_rate=0.08,
        inventory_days=30,
        delivery_history_days=90,
    )

    generator = ExternalSourceGenerator(
        engine=engine,
        config=configuration,
    )

    print("2/5 Génération des retours CSV...")

    return_count = generator.generate_returns(RETURNS_DIRECTORY)

    print(f"   {return_count:,} retours générés.")

    print("3/5 Génération des snapshots d'inventaire...")

    inventory_count = generator.generate_inventory(INVENTORY_DIRECTORY)

    print(f"   {inventory_count:,} lignes d'inventaire.")

    print("4/5 Génération des événements de livraison...")

    delivery_event_count = generator.generate_deliveries(DELIVERY_FILE)

    print(f"   {delivery_event_count:,} événements logistiques.")

    print("5/5 Sources externes générées avec succès.")


if __name__ == "__main__":
    main()
