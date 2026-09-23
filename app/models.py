from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"


class LeadIn(BaseModel):
    """Payload de entrada del webhook — imita lo que manda un portal (ZonaProp/ML/formulario propio)."""

    source: str = Field(..., examples=["zonaprop", "web_form", "whatsapp"])
    full_name: str
    email: str
    phone: Optional[str] = None
    message: str = Field(..., description="Texto libre del lead describiendo qué busca")
    budget_usd: Optional[float] = None


class PropertyMatch(BaseModel):
    property_id: str
    title: str
    score: float


class Lead(BaseModel):
    id: str
    source: str
    full_name: str
    email: str
    phone: Optional[str] = None
    message: str
    budget_usd: Optional[float] = None
    status: LeadStatus = LeadStatus.warm
    summary: Optional[str] = None
    matches: list[PropertyMatch] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Property(BaseModel):
    id: str
    title: str
    description: str
    neighborhood: str
    price_usd: float
    bedrooms: int
