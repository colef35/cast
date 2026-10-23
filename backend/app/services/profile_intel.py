"""
Profile intelligence — generic, product-agnostic helpers that resolve every
piece of product-specific behaviour from a ProductProfile record.

Nothing in this module (or in the scanners / scorer that call it) knows about
any particular product. A product supplies its specifics as profile data
(SPEC §4.1); the generic defaults below apply only when a profile leaves a
field empty, so a brand-new product with just a name, keywords and a URL
still scans, scores and drafts sensibly.
"""
from app.models.product_profile import ProductProfile

# Generic buying-intent phrases — used only when a profile defines none.
DEFAULT_BUYING_SIGNALS = [
    "looking for", "recommend", "any suggestions", "what do you use",
    "alternative to", "too expensive", "frustrated with", "manual process",
    "spreadsheet", "pain point", "problem with", "wish there was",
    "does anyone know", "how do you handle", "what's your workflow",
    "switching from", "worth it", "which tool",
]

# Generic noise markers — used only when a profile defines none.
DEFAULT_REJECT_SIGNALS = [
    "cryptocurrency", "blockchain", "bootcamp", "tech recruiter",
    "immigration", "health insurance", "software contractor",
    "software engineer", "software developer", "programmer",
]

# Generic draft voices — helpful first, product second. Placeholders:
# {name} {feature} {url} {tagline}. Used only when the profile's
# voice.draft_templates has no entry for the channel.
DEFAULT_DRAFT_TEMPLATES = {
    "hackernews": (
        "We built {name} specifically for this — {feature} is one of the core "
        "workflows. More here if useful: {url}. Happy to answer questions."
    ),
    "reddit": (
        "This is exactly why we built {name}. {feature} — it's the core of "
        "{tagline}. {url}"
    ),
    "linkedin": (
        "Relevant here — {name} was built for exactly this problem. "
        "{feature}. {url}"
    ),
    "twitter": "Built for this → {name} covers {feature}. {url}",
    "web": (
        "This is exactly why we built {name}. {feature} — it's the core of "
        "{tagline}. {url}"
    ),
    "youtube": (
        "This is exactly why we built {name}. {feature} — it's the core of "
        "{tagline}. {url}"
    ),
    "forum": (
        "This is exactly why we built {name}. {feature} — it's the core of "
        "{tagline}. {url}"
    ),
}


def get_buying_signals(product: ProductProfile) -> list[str]:
    return product.buying_signals or DEFAULT_BUYING_SIGNALS


def get_reject_signals(product: ProductProfile) -> list[str]:
    return product.reject_signals or DEFAULT_REJECT_SIGNALS


def is_blocked(product: ProductProfile, community_or_url: str) -> bool:
    target = (community_or_url or "").lower()
    return any(b and b.lower() in target for b in product.blocked_communities)


def get_communities(product: ProductProfile, platform: str) -> list[str]:
    """Target communities for a platform, minus anything blocked."""
    return [
        c for c in product.communities.get(platform, [])
        if not is_blocked(product, c)
    ]


def get_search_queries(product: ProductProfile, channel: str) -> list[str]:
    return product.search_queries.get(channel, [])


def derive_search_queries(product: ProductProfile) -> list[str]:
    """Fallback queries built from the profile itself (keywords, problem
    phrases, competitors) when a channel has no configured queries."""
    queries = list(product.keywords[:6])
    queries += list(product.problem_phrases[:4])
    queries += [f"alternative to {c}" for c in product.competitors[:3]]
    return queries


def get_relevance_signals(product: ProductProfile, channel: str) -> list[str]:
    """Topical vocabulary a hit must touch to count as relevant on a channel."""
    signals = product.relevance_signals.get(channel) or product.domain_signals
    if signals:
        return [s.lower() for s in signals]
    vocab = list(product.keywords) + list(product.competitors)
    return [v.lower() for v in vocab]


def get_draft_template(product: ProductProfile, channel: str) -> str:
    templates = product.voice.draft_templates or {}
    return (
        templates.get(channel)
        or templates.get("reddit")
        or DEFAULT_DRAFT_TEMPLATES.get(channel)
        or DEFAULT_DRAFT_TEMPLATES["reddit"]
    )


def fallback_feature(product: ProductProfile) -> str:
    if product.default_feature:
        return product.default_feature
    if product.pitch_points:
        return product.pitch_points[0]
    return product.tagline


def detect_feature(product: ProductProfile, text: str) -> str:
    """Map post text → the profile feature to highlight in a draft."""
    lowered = text.lower()
    for mapping in product.feature_map:
        if any(k.lower() in lowered for k in mapping.keywords):
            return mapping.feature
    return fallback_feature(product)
