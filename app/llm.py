"""Clasificación del lead (hot/warm/cold) + resumen usando Claude.

Diseñado para ser testeable sin pegarle a la API real: si no hay
ANTHROPIC_API_KEY configurada, cae a un clasificador heurístico simple
(mock) en vez de fallar. Esto es lo que permite correr `pytest` en CI
sin secretos ni costo.
"""
from __future__ import annotations

import json
import logging

from anthropic import Anthropic

from app.config import settings
from app.models import LeadStatus

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Sos un asistente que clasifica leads inmobiliarios. Dado el mensaje de un "
    "lead y su presupuesto, respondé SOLO un JSON con las claves "
    '"status" (hot|warm|cold) y "summary" (una frase breve en español).'
)


def _mock_classify(message: str, budget_usd: float | None) -> tuple[LeadStatus, str]:
    """Heurística simple usada cuando no hay API key (dev/test/CI)."""
    text = message.lower()
    urgent_words = ("urgente", "esta semana", "ya", "cuanto antes", "hoy")
    status = LeadStatus.warm
    if any(w in text for w in urgent_words) or (budget_usd and budget_usd > 300_000):
        status = LeadStatus.hot
    elif len(text) < 15:
        status = LeadStatus.cold
    return status, f"Lead heurístico (sin LLM): interesado en '{message[:60]}'"


def classify_lead(message: str, budget_usd: float | None = None) -> tuple[LeadStatus, str]:
    if not settings.anthropic_api_key:
        return _mock_classify(message, budget_usd)

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Mensaje: {message}\nPresupuesto USD: {budget_usd}",
                }
            ],
        )
        payload = json.loads(response.content[0].text)
        return LeadStatus(payload["status"]), payload["summary"]
    except Exception:
        logger.exception("Fallo la clasificación con Claude, uso heurística de respaldo")
        return _mock_classify(message, budget_usd)
