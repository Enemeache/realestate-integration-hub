from typing import Optional

import strawberry

from app.db import get_db
from app.models import LeadStatus
from app.repository import list_leads


@strawberry.type
class PropertyMatchType:
    property_id: str
    title: str
    score: float


@strawberry.type
class LeadType:
    id: str
    source: str
    full_name: str
    email: str
    status: str
    summary: Optional[str]
    matches: list[PropertyMatchType]


@strawberry.type
class Query:
    @strawberry.field
    async def leads(self, status: Optional[str] = None) -> list[LeadType]:
        parsed_status = LeadStatus(status) if status else None
        db = get_db()
        leads = await list_leads(db, status=parsed_status)
        return [
            LeadType(
                id=lead.id,
                source=lead.source,
                full_name=lead.full_name,
                email=lead.email,
                status=lead.status.value,
                summary=lead.summary,
                matches=[
                    PropertyMatchType(property_id=m.property_id, title=m.title, score=m.score)
                    for m in lead.matches
                ],
            )
            for lead in leads
        ]


schema = strawberry.Schema(query=Query)
