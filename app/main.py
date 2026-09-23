import logging
from typing import Callable, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from strawberry.fastapi import GraphQLRouter

from app.config import settings
from app.db import get_db
from app.graphql_schema import schema
from app.logging_conf import configure_logging
from app.models import Lead, LeadIn, LeadStatus
from app.queue import publish_lead
from app.repository import get_lead, list_leads, new_lead_id
from app.security import verify_signature

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PropLeads Integration Hub",
    description=(
        "Demo de integración: webhook de leads inmobiliarios -> cola -> worker "
        "con matching semántico + clasificación IA -> REST/GraphQL."
    ),
    version="0.1.0",
)

app.include_router(GraphQLRouter(schema), prefix="/graphql")


def get_queue_publisher() -> Callable[[dict], None]:
    """Punto de inyección: los tests lo overridean para no requerir RabbitMQ real."""
    return publish_lead


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook/lead", status_code=status.HTTP_202_ACCEPTED, tags=["leads"])
async def receive_lead(
    request: Request,
    lead_in: LeadIn,
    x_signature: Optional[str] = Header(default=None, alias="X-Signature"),
    publisher: Callable[[dict], None] = Depends(get_queue_publisher),
):
    """Recibe un lead de un portal/formulario externo y lo encola para procesamiento asíncrono.

    Si `WEBHOOK_SECRET` está configurado, exige el header `X-Signature` con el
    HMAC-SHA256 (hex) del body crudo firmado con ese secreto — mismo patrón que
    usan los portales reales (y Stripe) para que solo el emisor legítimo pueda
    publicar leads.
    """
    if settings.webhook_secret:
        raw_body = await request.body()
        if not verify_signature(settings.webhook_secret, raw_body, x_signature):
            raise HTTPException(status_code=401, detail="Firma invalida o ausente")

    lead_id = new_lead_id()
    payload = {"id": lead_id, **lead_in.model_dump()}
    try:
        publisher(payload)
    except Exception:
        logger.exception("No se pudo publicar el lead %s en la cola", lead_id)
        raise HTTPException(status_code=503, detail="Cola de mensajería no disponible")
    return {"id": lead_id, "queued": True}


@app.get("/leads/{lead_id}", response_model=Lead, tags=["leads"])
async def read_lead(lead_id: str):
    db = get_db()
    lead = await get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return lead


@app.get("/leads", response_model=list[Lead], tags=["leads"])
async def read_leads(status_filter: Optional[LeadStatus] = None):
    db = get_db()
    return await list_leads(db, status=status_filter)
