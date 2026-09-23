"""Worker: consume la cola de leads, hace matching + clasificación, guarda en Mongo.

Corre como proceso separado del API (ver docker-compose.yml, servicio `worker`).
Usa pymongo (sync) porque pika.BlockingConnection es sync y no comparte loop
con motor (async), que sí usa el servicio API para las lecturas.
"""
import logging

from pymongo import MongoClient

from app.config import settings
from app.llm import classify_lead
from app.logging_conf import configure_logging
from app.matching import build_matcher
from app.queue import consume_leads
from app.repository import lead_to_document, load_properties

configure_logging()
logger = logging.getLogger(__name__)

_properties = load_properties()
_matcher = build_matcher(_properties, engine=settings.embedding_engine)
_mongo = MongoClient(settings.mongo_uri)[settings.mongo_db]


def handle_lead(payload: dict) -> None:
    lead_id = payload["id"]
    logger.info("Procesando lead %s de %s", lead_id, payload.get("source"))

    matches = _matcher.top_matches(payload["message"], k=3)
    status, summary = classify_lead(payload["message"], payload.get("budget_usd"))

    document = lead_to_document(lead_id, payload, status, summary, matches)
    _mongo.leads.insert_one(document)
    logger.info("Lead %s guardado con status=%s, %d matches", lead_id, status.value, len(matches))


if __name__ == "__main__":
    consume_leads(handle_lead)
