import json
from pathlib import Path
from uuid import uuid4

from app.models import Lead, LeadStatus, Property, PropertyMatch

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "properties_seed.json"


def load_properties() -> list[Property]:
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return [Property(**item) for item in raw]


def new_lead_id() -> str:
    return str(uuid4())


async def insert_lead(db, lead: Lead) -> None:
    await db.leads.insert_one(lead.model_dump(mode="json"))


async def get_lead(db, lead_id: str) -> Lead | None:
    doc = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return Lead(**doc) if doc else None


async def list_leads(db, status: LeadStatus | None = None, limit: int = 50) -> list[Lead]:
    query = {"status": status.value} if status else {}
    cursor = db.leads.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [Lead(**doc) async for doc in cursor]


def lead_to_document(
    lead_id: str,
    payload: dict,
    status: LeadStatus,
    summary: str,
    matches: list[PropertyMatch],
) -> dict:
    lead = Lead(
        id=lead_id,
        source=payload["source"],
        full_name=payload["full_name"],
        email=payload["email"],
        phone=payload.get("phone"),
        message=payload["message"],
        budget_usd=payload.get("budget_usd"),
        status=status,
        summary=summary,
        matches=matches,
    )
    return lead.model_dump(mode="json")
