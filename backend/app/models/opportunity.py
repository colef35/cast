from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class OpportunityStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    sent = "sent"


class Channel(str, Enum):
    hackernews = "hackernews"
    reddit = "reddit"
    linkedin = "linkedin"
    twitter = "twitter"


class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    product_id: UUID
    user_id: UUID
    channel: Channel
    source_url: str
    source_title: str
    source_body: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    roi_score: float = Field(ge=0.0, le=1.0)
    draft: Optional[str] = None
    status: OpportunityStatus = OpportunityStatus.pending
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acted_at: Optional[datetime] = None


class OpportunityCreate(BaseModel):
    product_id: UUID
    user_id: UUID
    channel: Channel
    source_url: str
    source_title: str
    source_body: str
