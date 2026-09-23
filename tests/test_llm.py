from app.llm import classify_lead
from app.models import LeadStatus


def test_classify_lead_falls_back_to_heuristic_without_api_key(monkeypatch):
    monkeypatch.setattr("app.llm.settings.anthropic_api_key", None)

    status, summary = classify_lead("Necesito mudarme urgente esta semana", budget_usd=100_000)

    assert status == LeadStatus.hot
    assert "heurístico" in summary.lower()


def test_classify_lead_high_budget_is_hot(monkeypatch):
    monkeypatch.setattr("app.llm.settings.anthropic_api_key", None)

    status, _ = classify_lead("Estoy mirando opciones para el futuro", budget_usd=400_000)

    assert status == LeadStatus.hot


def test_classify_lead_short_message_is_cold(monkeypatch):
    monkeypatch.setattr("app.llm.settings.anthropic_api_key", None)

    status, _ = classify_lead("hola", budget_usd=None)

    assert status == LeadStatus.cold
