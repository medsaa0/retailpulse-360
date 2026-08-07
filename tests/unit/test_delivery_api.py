"""Tests de l'API logistique."""

import json

from fastapi.testclient import TestClient

import delivery_api.main as api_module


def create_test_file(
    tmp_path,
) -> None:
    """Créer des événements temporaires."""

    events = [
        {
            "delivery_id": "DEL-000000001",
            "order_id": "ORD-000000001",
            "carrier": "Atlas Express",
            "delivery_status": "IN_TRANSIT",
            "event_timestamp": ("2026-08-05T10:00:00Z"),
            "shipping_date": "2026-08-05",
            "expected_delivery_date": ("2026-08-08"),
            "actual_delivery_date": None,
            "destination_city": "Oujda",
        },
        {
            "delivery_id": "DEL-000000001",
            "order_id": "ORD-000000001",
            "carrier": "Atlas Express",
            "delivery_status": "DELIVERED",
            "event_timestamp": ("2026-08-08T14:00:00Z"),
            "shipping_date": "2026-08-05",
            "expected_delivery_date": ("2026-08-08"),
            "actual_delivery_date": ("2026-08-08"),
            "destination_city": "Oujda",
        },
    ]

    file_path = tmp_path / "delivery_events.json"

    file_path.write_text(
        json.dumps(events),
        encoding="utf-8",
    )

    api_module.DATA_FILE = file_path


def test_health_endpoint(
    tmp_path,
) -> None:
    """Vérifier le endpoint health."""

    create_test_file(tmp_path)

    client = TestClient(api_module.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_deliveries_endpoint(
    tmp_path,
) -> None:
    """Vérifier la liste des livraisons."""

    create_test_file(tmp_path)

    client = TestClient(api_module.app)

    response = client.get("/api/v1/deliveries")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 2
    assert len(payload["data"]) == 2


def test_filter_deliveries_by_status(
    tmp_path,
) -> None:
    """Vérifier le filtre par statut."""

    create_test_file(tmp_path)

    client = TestClient(api_module.app)

    response = client.get(
        "/api/v1/deliveries",
        params={
            "status": "DELIVERED",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1

    assert payload["data"][0]["delivery_status"] == "DELIVERED"


def test_delivery_history(
    tmp_path,
) -> None:
    """Vérifier l'historique d'une livraison."""

    create_test_file(tmp_path)

    client = TestClient(api_module.app)

    response = client.get("/api/v1/deliveries/DEL-000000001")

    assert response.status_code == 200
    assert len(response.json()) == 2
