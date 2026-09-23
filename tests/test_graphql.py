from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app import graphql_schema
from app.main import app
from app.models import Lead, PropertyMatch


def _seed_mock_db():
    mock_client = AsyncMongoMockClient()
    return mock_client["propleads_test"]


def test_graphql_leads_query_returns_seeded_lead(monkeypatch):
    mock_db = _seed_mock_db()
    monkeypatch.setattr(graphql_schema, "get_db", lambda: mock_db)

    lead = Lead(
        id="lead-1",
        source="web_form",
        full_name="Ana Gomez",
        email="ana@example.com",
        message="busco depto 2 ambientes",
        status="hot",
        summary="Lead interesado",
        matches=[PropertyMatch(property_id="p1", title="Depto test", score=0.9)],
    )

    import asyncio

    asyncio.get_event_loop().run_until_complete(
        mock_db.leads.insert_one(lead.model_dump(mode="json"))
    )

    client = TestClient(app)
    query = "{ leads(status: \"hot\") { id fullName status matches { title score } } }"
    # strawberry expone camelCase por defecto para los campos snake_case
    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload
    leads = payload["data"]["leads"]
    assert len(leads) == 1
    assert leads[0]["fullName"] == "Ana Gomez"
    assert leads[0]["matches"][0]["title"] == "Depto test"
