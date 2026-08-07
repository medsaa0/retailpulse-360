"""Point d'entrée pour générer et charger les données source."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from data_generator.config import GenerationConfig
from data_generator.generator import RetailDataGenerator
from data_generator.loader import (
    count_rows,
    create_postgres_engine,
    load_generated_data,
    wait_for_database,
)


def parse_arguments() -> argparse.Namespace:
    """Lire les options depuis la ligne de commande."""

    parser = argparse.ArgumentParser(
        description=("Générer et charger les données source RetailPulse 360.")
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=2_000,
    )

    parser.add_argument(
        "--products",
        type=int,
        default=250,
    )

    parser.add_argument(
        "--stores",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--orders",
        type=int,
        default=10_000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help=("Ajouter les données sans vider les tables avant le chargement."),
    )

    return parser.parse_args()


def main() -> None:
    """Générer et charger les données."""

    arguments = parse_arguments()

    configuration = GenerationConfig(
        customer_count=arguments.customers,
        product_count=arguments.products,
        store_count=arguments.stores,
        order_count=arguments.orders,
        seed=arguments.seed,
        end_date=datetime.now(UTC).replace(microsecond=0),
    )

    print("1/4 Génération des données...")

    generator = RetailDataGenerator(configuration)

    datasets = generator.generate_all()

    for table_name, rows in datasets.items():
        print(f"   {table_name}: {len(rows):,} lignes")

    print("2/4 Connexion à PostgreSQL...")

    engine = create_postgres_engine()
    wait_for_database(engine)

    print("3/4 Chargement dans le schéma source...")

    load_generated_data(
        engine,
        datasets,
        reset=not arguments.append,
    )

    print("4/4 Vérification des volumes...")

    counts = count_rows(engine)

    for table_name, row_count in counts.items():
        print(f"   source.{table_name}: {row_count:,} lignes")

    print("Chargement terminé avec succès.")


if __name__ == "__main__":
    main()
