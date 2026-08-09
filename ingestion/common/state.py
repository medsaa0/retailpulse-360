"""État persistant du pipeline d'ingestion."""

from __future__ import annotations

from typing import Any

from ingestion.common.storage import ObjectStorage

STATE_KEY = "_control/ingestion_state.json"


def default_state() -> dict[str, Any]:
    """Créer un état initial."""

    return {
        "version": 1,
        "postgres_watermarks": {},
        "delivery_watermark": None,
        "processed_files": {},
    }


def load_state(
    storage: ObjectStorage,
) -> dict[str, Any]:
    """Charger l'état d'ingestion."""

    state = storage.get_json(
        STATE_KEY,
        default_state(),
    )

    defaults = default_state()

    for key, value in defaults.items():
        state.setdefault(
            key,
            value,
        )

    return state


def save_state(
    storage: ObjectStorage,
    state: dict[str, Any],
) -> None:
    """Sauvegarder l'état du pipeline."""

    storage.put_json(
        STATE_KEY,
        state,
    )
