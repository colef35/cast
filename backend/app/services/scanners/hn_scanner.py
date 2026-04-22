import httpx
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
MIN_POINTS = 3
MIN_COMMENTS = 1


async def scan_hn(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    queries = DATUM_PROFILE["hn_queries"] if product.name == "DATUM+ Field OS" else product.keywords[:5]

    async with httpx.AsyncClient() as client:
        for query in queries:
            for tag in ["story", "ask_hn"]:
                resp = await client.get(ALGOLIA_URL, params={
                    "query": query,
                    "tags": tag,
                    "numericFilters": f"points>={MIN_POINTS},num_comments>={MIN_COMMENTS}",
                    "hitsPerPage": 8,
                })
                resp.raise_for_status()
                for hit in resp.json().get("hits", []):
                    oid = hit.get("objectID")
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.hackernews,
                        source_url=f"https://news.ycombinator.com/item?id={oid}",
                        source_title=hit.get("title", ""),
                        source_body=(hit.get("story_text") or hit.get("url") or "")[:2000],
                    ))

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
