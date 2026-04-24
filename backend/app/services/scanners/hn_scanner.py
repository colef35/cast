import httpx
import time
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE
from app.core.proxy import proxy_kwargs

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
MIN_POINTS = 2
MIN_COMMENTS = 1
MAX_AGE_DAYS = 60  # only grab threads from the last 60 days (comment form still visible)

CONSTRUCTION_SIGNALS = [
    "construction", "excavat", "grading", "earthwork", "job cost",
    "procore", "buildertrend", "subcontract", "general contractor", "site work",
    "heavy equipment", "paving", "concrete", "framing", "field management",
    "punch list", "change order", "rfi", "submittal", "construction management",
    "construction software", "construction app", "construction scheduling",
    "construction payroll", "construction saas", "contractor software",
]

REJECT_SIGNALS = [
    "software contractor", "software engineer", "software developer",
    "programmer", "bootcamp", "tech recruiter", "immigration", "health insurance",
    "parallel construction", "intelligence agency", "law enforcement",
    "cryptocurrency", "blockchain",
]


def _is_relevant(title: str, body: str) -> bool:
    text = (title + " " + body).lower()
    if any(r in text for r in REJECT_SIGNALS):
        return False
    return any(s in text for s in CONSTRUCTION_SIGNALS)


async def scan_hn(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []

    cutoff = int(time.time()) - MAX_AGE_DAYS * 86400

    async with httpx.AsyncClient(**proxy_kwargs()) as client:
        for query in DATUM_PROFILE["hn_queries"]:
            for tag in ["story", "ask_hn"]:
                try:
                    resp = await client.get(ALGOLIA_URL, params={
                        "query": query,
                        "tags": tag,
                        "numericFilters": f"points>={MIN_POINTS},num_comments>={MIN_COMMENTS},created_at_i>{cutoff}",
                        "hitsPerPage": 20,
                    })
                    resp.raise_for_status()
                    for hit in resp.json().get("hits", []):
                        title = hit.get("title", "")
                        body = (hit.get("story_text") or hit.get("url") or "")[:2000]
                        if not _is_relevant(title, body):
                            continue
                        oid = hit.get("objectID")
                        opportunities.append(OpportunityCreate(
                            product_id=product.id,
                            user_id=product.user_id,
                            channel=Channel.hackernews,
                            source_url=f"https://news.ycombinator.com/item?id={oid}",
                            source_title=title,
                            source_body=body,
                        ))
                except Exception:
                    continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
