"""Lire target/run_results.json après 'dbt test' et enregistrer un résumé dans Snowflake."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from snowflake_load.client import get_connection

RUN_RESULTS_PATH = Path("dbt_retailpulse/target/run_results.json")


def main() -> None:
    if not RUN_RESULTS_PATH.exists():
        print(f"Fichier introuvable : {RUN_RESULTS_PATH}. Lance 'dbt test' d'abord.")
        sys.exit(1)

    run_results = json.loads(RUN_RESULTS_PATH.read_text(encoding="utf-8"))

    results = run_results.get("results", [])

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warned = sum(1 for r in results if r["status"] == "warn")
    total = len(results)

    if total == 0:
        print("Aucun résultat de test trouvé dans run_results.json.")
        sys.exit(1)

    pass_rate = round((passed / total) * 100, 2)
    status = "PASS" if failed == 0 else "FAIL"

    run_id = str(uuid4())
    executed_at = datetime.now(UTC).replace(microsecond=0)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO AUDIT.DATA_QUALITY_RESULTS
                    (run_id, executed_at, total_tests, passed_tests,
                     failed_tests, warned_tests, pass_rate_pct, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (run_id, executed_at, total, passed, failed, warned, pass_rate, status),
            )
            connection.commit()
    finally:
        connection.close()

    print(f"Qualité des données : {passed}/{total} tests passés ({pass_rate}%)")
    print(f"Statut global : {status}")

    if status == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()