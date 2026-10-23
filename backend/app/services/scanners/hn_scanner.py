import httpx
import time
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.profile_intel import (
    derive_search_queries,
    get_reject_signals,
    get_relevance_signals,
    get_search_queries,
)
from app.core.proxy import proxy_kwargs

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
MIN_POINTS = 2
MIN_COMMENTS = 1
MAX_AGE_DAYS = 7  # only grab threads from the last 7 days (comment form visible on fresh threads)


def _is_relevant(title: str, body: str, signals: list[str], reject_signals: list[str]) -> bool:
    text = (title + " " + body).lower()
    if any(r in text for r in reject_signals):
        return False
    return any(s in text for s in signals)


async def scan_hn(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []

    # Queries, relevance vocabulary and reject list all come from the
    # profile (SPEC §4.1); generic fallbacks derive from its keywords.
    queries = get_search_queries(product, "hackernews") or derive_search_queries(product)
    signals = get_relevance_signals(product, "hackernews")
    reject_signals = [r.lower() for r in get_reject_signals(product)]

    cutoff = int(time.time()) - MAX_AGE_DAYS * 86400

    async with httpx.AsyncClient(**proxy_kwargs()) as client:
        for query in queries:
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
                        if not _is_relevant(title, body, signals, reject_signals):
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
