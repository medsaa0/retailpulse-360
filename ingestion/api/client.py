"""Client HTTP pour l'API de livraison."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from ingestion.common.settings import get_settings


def _iso_utc(
    value: datetime,
) -> str:
    """Convertir une date au format ISO UTC."""

    return (
        value.astimezone(UTC)
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def fetch_delivery_events(
    watermark: datetime | None,
) -> list[dict[str, Any]]:
    """Récupérer tous les événements nouveaux."""

    settings = get_settings()

    base_url = settings.delivery_api_base_url.rstrip("/")

    limit = 1000
    offset = 0

    events: list[dict[str, Any]] = []

    while True:
        parameters: dict[str, str | int] = {
            "offset": offset,
            "limit": limit,
        }

        if watermark is not None:
            parameters["updated_since"] = _iso_utc(watermark)

        url = f"{base_url}/api/v1/deliveries?{urlencode(parameters)}"

        with urlopen(
            url,
            timeout=30,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))

        page = payload["data"]

        events.extend(page)

        total = int(payload["total"])

        offset += len(page)

        if not page or offset >= total:
            break

    return events
