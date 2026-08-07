"""API REST exposant les événements de livraison."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)
from pydantic import BaseModel

ROOT_DIRECTORY = Path(__file__).resolve().parents[1]

DATA_FILE = ROOT_DIRECTORY / "source_data" / "deliveries" / "delivery_events.json"


class DeliveryEvent(BaseModel):
    """Événement logistique exposé par l'API."""

    delivery_id: str
    order_id: str
    carrier: str
    delivery_status: str
    event_timestamp: datetime
    shipping_date: date
    expected_delivery_date: date
    actual_delivery_date: date | None
    destination_city: str


class DeliveryResponse(BaseModel):
    """Réponse paginée de l'API."""

    total: int
    offset: int
    limit: int
    data: list[DeliveryEvent]


app = FastAPI(
    title="RetailPulse Delivery API",
    description=("API logistique simulée utilisée comme source de données par RetailPulse 360."),
    version="1.0.0",
)


def load_events() -> list[DeliveryEvent]:
    """Charger les événements depuis le fichier source."""

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail=("Les données de livraison n'ont pas encore été générées."),
        )

    with DATA_FILE.open(encoding="utf-8") as file:
        raw_events = json.load(file)

    return [DeliveryEvent.model_validate(event) for event in raw_events]


@app.get("/health")
def health() -> dict[str, str | bool]:
    """Vérifier la disponibilité de l'API."""

    return {
        "status": "ok",
        "data_file_exists": DATA_FILE.exists(),
    }


@app.get(
    "/api/v1/deliveries",
    response_model=DeliveryResponse,
)
def get_deliveries(
    updated_since: datetime | None = None,
    status: str | None = None,
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> DeliveryResponse:
    """Retourner les événements avec filtres."""

    events = load_events()

    if updated_since is not None:
        events = [event for event in events if event.event_timestamp > updated_since]

    if status is not None:
        normalized_status = status.upper()

        events = [event for event in events if event.delivery_status == normalized_status]

    total = len(events)

    paginated_events = events[offset : offset + limit]

    return DeliveryResponse(
        total=total,
        offset=offset,
        limit=limit,
        data=paginated_events,
    )


@app.get(
    "/api/v1/deliveries/{delivery_id}",
    response_model=list[DeliveryEvent],
)
def get_delivery_history(
    delivery_id: str,
) -> list[DeliveryEvent]:
    """Retourner l'historique d'une livraison."""

    events = [event for event in load_events() if event.delivery_id == delivery_id]

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Livraison introuvable.",
        )

    return events
