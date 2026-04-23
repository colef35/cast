import os
import httpx
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

UA = "Mozilla/5.0 (compatible; cast-bot/0.1)"
MIN_SCORE = 0
MIN_COMMENTS = 0


async def scan_reddit(product: ProductProfile) -> list[OpportunityCreate]:
    subreddits = DATUM_PROFILE["subreddits"]
    keywords = product.keywords[:4] if product.keywords else DATUM_PROFILE["keywords"][:4]

    opportunities = []
    seen = set()

    async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=15) as client:
        for subreddit in subreddits[:8]:
            for keyword in keywords[:4]:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/search.json",
                        params={"q": keyword, "sort": "new", "restrict_sr": "true", "limit": 10, "t": "month"},
                    )
                    if resp.status_code != 200:
                        continue
                    posts = resp.json().get("data", {}).get("children", [])
                    for post in posts:
                        d = post["data"]
                        if d.get("score", 0) < MIN_SCORE or d.get("num_comments", 0) < MIN_COMMENTS:
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

    return opportunities
