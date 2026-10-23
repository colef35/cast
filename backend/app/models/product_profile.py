from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class VoiceProfile(BaseModel):
    """How a product sounds when CAST drafts for it (SPEC §4.1)."""

    # Tone sliders, 0.0–1.0 (e.g. formality, humor, technical_depth, directness).
    tone: dict[str, float] = {}
    # Example posts in the owner's own words.
    example_posts: list[str] = []
    # Per-channel draft templates. Placeholders: {name} {feature} {url} {tagline}.
    draft_templates: dict[str, str] = {}


class Guardrails(BaseModel):
    """Claims and topics CAST must never touch for a product (SPEC §4.1)."""

    forbidden_claims: list[str] = []
    avoid_topics: list[str] = []
    disclose_ai: bool = False


class FeatureMapping(BaseModel):
    """Pain keywords → the product feature to highlight in a draft."""

    keywords: list[str] = []
    feature: str


class ProductProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    # Workspace this profile belongs to (SPEC §4.2). Optional during the
    # Phase 0 transition — profiles created before workspaces have none and
    # are owned directly by user_id, exactly as before.
    workspace_id: Optional[UUID] = None
    name: str
    tagline: str
    description: str
    target_audience: str
    pain_point_solved: str
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    pricing_url: Optional[str] = None
    keywords: list[str] = []

    # ── SPEC §4.1 profile fields ──────────────────────────────────────────
    # Pitch points + proof points (user-supplied, never invented).
    pitch_points: list[str] = []
    proof_points: list[str] = []
    # Phrases buyers use when they have the problem this product solves.
    problem_phrases: list[str] = []
    competitors: list[str] = []
    # Target communities per platform, e.g. {"reddit": ["SaaS", ...],
    # "forum": ["https://…/section/"]}.
    communities: dict[str, list[str]] = {}
    # Communities CAST must never engage, any platform.
    blocked_communities: list[str] = []
    # Buying-intent phrases the scanners/scorer listen for.
    buying_signals: list[str] = []
    # Topical vocabulary of the product's world (relevance gate fallback).
    domain_signals: list[str] = []
    # Per-channel relevance vocabulary, e.g. {"hackernews": [...], "forum": [...]}.
    relevance_signals: dict[str, list[str]] = {}
    # Phrases that mark a hit as noise (staffing ads, crypto spam, …).
    reject_signals: list[str] = []
    # Per-channel search queries, e.g. {"web": [...], "youtube": [...],
    # "hackernews": [...], "quora": [...]}.
    search_queries: dict[str, list[str]] = {}
    # Pain keywords → feature to highlight (drives draft drafting).
    feature_map: list[FeatureMapping] = []
    # Feature used when no feature_map entry matches.
    default_feature: Optional[str] = None
    # Free tools / lead magnets the drafts may point at.
    free_tools: list[str] = []
    voice: VoiceProfile = Field(default_factory=VoiceProfile)
    guardrails: Guardrails = Field(default_factory=Guardrails)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductProfileCreate(BaseModel):
    workspace_id: Optional[UUID] = None
    name: str
    tagline: str
    description: str
    target_audience: str
    pain_point_solved: str
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    pricing_url: Optional[str] = None
    keywords: list[str] = []
    pitch_points: list[str] = []
    proof_points: list[str] = []
    problem_phrases: list[str] = []
    competitors: list[str] = []
    communities: dict[str, list[str]] = {}
    blocked_communities: list[str] = []
    buying_signals: list[str] = []
    domain_signals: list[str] = []
    relevance_signals: dict[str, list[str]] = {}
    reject_signals: list[str] = []
    search_queries: dict[str, list[str]] = {}
    feature_map: list[FeatureMapping] = []
    default_feature: Optional[str] = None
    free_tools: list[str] = []
    voice: VoiceProfile = Field(default_factory=VoiceProfile)
    guardrails: Guardrails = Field(default_factory=Guardrails)


class ProductProfileUpdate(BaseModel):
    workspace_id: Optional[UUID] = None
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    target_audience: Optional[str] = None
    pain_point_solved: Optional[str] = None
    url: Optional[str] = None
    pricing_summary: Optional[str] = None
    pricing_url: Optional[str] = None
    keywords: Optional[list[str]] = None
    pitch_points: Optional[list[str]] = None
    proof_points: Optional[list[str]] = None
    problem_phrases: Optional[list[str]] = None
    competitors: Optional[list[str]] = None
    communities: Optional[dict[str, list[str]]] = None
    blocked_communities: Optional[list[str]] = None
    buying_signals: Optional[list[str]] = None
    domain_signals: Optional[list[str]] = None
    relevance_signals: Optional[dict[str, list[str]]] = None
    reject_signals: Optional[list[str]] = None
    search_queries: Optional[dict[str, list[str]]] = None
    feature_map: Optional[list[FeatureMapping]] = None
    default_feature: Optional[str] = None
    free_tools: Optional[list[str]] = None
    voice: Optional[VoiceProfile] = None
    guardrails: Optional[Guardrails] = None
