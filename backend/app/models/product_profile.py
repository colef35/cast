from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class ProductProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str
    tagline: str
    description: str
    target_audience: str
    pain_point_solved: str
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    keywords: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductProfileCreate(BaseModel):
    name: str
    tagline: str
    description: str
    target_audience: str
    pain_point_solved: str
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    keywords: list[str] = []


class ProductProfileUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    target_audience: Optional[str] = None
    pain_point_solved: Optional[str] = None
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    keywords: Optional[list[str]] = None
