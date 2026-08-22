"""Créer les objets Snowflake nécessaires au projet."""

from pathlib import Path

from snowflake_load.client import get_connection

ROOT_DIRECTORY = Path(__file__).resolve().parents[1]

SQL_FILE = (
    ROOT_DIRECTORY
    / "snowflake_sql"
    / "001_bootstrap.sql"
)


def main() -> None:
    """Exécuter le script SQL d'initialisation."""

    print("Connexion à Snowflake...")

    connection = get_connection(
        include_context=False
    )

    try:
        with SQL_FILE.open(
            encoding="utf-8-sig"
        ) as sql_stream:
            cursors = connection.execute_stream(
                sql_stream,
                remove_comments=True,
            )

            statement_count = 0

            for cursor in cursors:
                statement_count += 1

                print(
                    "[OK] statement "
                    f"{statement_count} "
                    f"| query_id={cursor.sfqid}"
                )

        print(
            "Bootstrap Snowflake terminé "
            "avec succès."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
