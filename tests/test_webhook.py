from fastapi.testclient import TestClient

from app.main import app, get_queue_publisher


def test_webhook_queues_lead_and_returns_202():
    published = []
    app.dependency_overrides[get_queue_publisher] = lambda: published.append

    client = TestClient(app)
    body = {
        "source": "web_form",
        "full_name": "Juana Perez",
        "email": "juana@example.com",
        "message": "Busco una casa con pileta para mi familia, urgente esta semana",
        "budget_usd": 300000,
    }

    response = client.post("/webhook/lead", json=body)

    assert response.status_code == 202
    data = response.json()
    assert data["queued"] is True
    assert "id" in data
    assert published[0]["full_name"] == "Juana Perez"

    app.dependency_overrides.clear()


def test_webhook_rejects_invalid_payload():
    client = TestClient(app)

    response = client.post("/webhook/lead", json={"source": "web_form"})

    assert response.status_code == 422


def test_webhook_returns_503_when_queue_unavailable():
    def _broken_publisher(_payload):
        raise ConnectionError("rabbitmq unreachable")

    app.dependency_overrides[get_queue_publisher] = lambda: _broken_publisher

    client = TestClient(app)
    body = {
        "source": "web_form",
        "full_name": "Juan",
        "email": "j@example.com",
        "message": "hola",
    }

    response = client.post("/webhook/lead", json=body)

    assert response.status_code == 503
    app.dependency_overrides.clear()
