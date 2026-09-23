import json

from fastapi.testclient import TestClient

from app.main import app, get_queue_publisher
from app.security import compute_signature

BODY = {
    "source": "zonaprop",
    "full_name": "Carla Diaz",
    "email": "carla@example.com",
    "message": "Busco un departamento de 2 ambientes",
}


def _client_with_stub_publisher():
    app.dependency_overrides[get_queue_publisher] = lambda: (lambda payload: None)
    return TestClient(app)


def test_webhook_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr("app.main.settings.webhook_secret", "supersecreto")
    raw = json.dumps(BODY).encode()
    signature = compute_signature("supersecreto", raw)

    client = _client_with_stub_publisher()
    response = client.post(
        "/webhook/lead", content=raw, headers={"Content-Type": "application/json", "X-Signature": signature}
    )

    assert response.status_code == 202
    app.dependency_overrides.clear()


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr("app.main.settings.webhook_secret", "supersecreto")
    raw = json.dumps(BODY).encode()

    client = _client_with_stub_publisher()
    response = client.post(
        "/webhook/lead",
        content=raw,
        headers={"Content-Type": "application/json", "X-Signature": "firma-trucha"},
    )

    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_webhook_rejects_missing_signature(monkeypatch):
    monkeypatch.setattr("app.main.settings.webhook_secret", "supersecreto")

    client = _client_with_stub_publisher()
    response = client.post("/webhook/lead", json=BODY)

    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_webhook_skips_check_when_no_secret_configured(monkeypatch):
    monkeypatch.setattr("app.main.settings.webhook_secret", None)

    client = _client_with_stub_publisher()
    response = client.post("/webhook/lead", json=BODY)

    assert response.status_code == 202
    app.dependency_overrides.clear()
