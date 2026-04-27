import httpx
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE
from app.core.proxy import proxy_kwargs

UA = "cast-bot/0.1 by u/ColeFar89"
MAX_AGE_DAYS = 14


async def scan_reddit(product: ProductProfile) -> list[OpportunityCreate]:
    subreddits = DATUM_PROFILE["subreddits"]
    keywords = product.keywords[:5] if product.keywords else DATUM_PROFILE["keywords"][:5]

    opportunities = []
    seen = set()

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=15,
        headers={"User-Agent": UA},
        **proxy_kwargs(),
    ) as client:
        for subreddit in subreddits[:10]:
            for keyword in keywords[:3]:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/search.json",
                        params={
                            "q": keyword,
                            "sort": "new",
                            "restrict_sr": "true",
                            "limit": 15,
                            "t": "month",
                        },
                    )
                    if resp.status_code != 200:
                        continue
                    posts = resp.json().get("data", {}).get("children", [])
                    for post in posts:
                        d = post["data"]
                        if d.get("score", 0) < 1:
                            continue
                        url = f"https://reddit.com{d['permalink']}"
                        if url in seen:
                            continue
                        seen.add(url)
                        opportunities.append(OpportunityCreate(
                            product_id=product.id,
                            user_id=product.user_id,
                            channel=Channel.reddit,
                            source_url=url,
                            source_title=d.get("title", ""),
                            source_body=(d.get("selftext") or "")[:2000],
                        ))
                except Exception:
                    continue

    seen_final, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen_final:
            seen_final.add(o.source_url)
            deduped.append(o)
    return deduped
