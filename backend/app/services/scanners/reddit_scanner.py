import os
import httpx
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
MIN_SCORE = 3
MIN_COMMENTS = 1


async def _get_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
        headers={"User-Agent": os.environ.get("REDDIT_USER_AGENT", "cast-bot/0.1")},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def scan_reddit(product: ProductProfile) -> list[OpportunityCreate]:
    if not os.environ.get("REDDIT_CLIENT_ID"):
        return []

    opportunities = []
    subreddits = DATUM_PROFILE["subreddits"] if product.name == "DATUM+ Field OS" else ["all"]
    keywords = product.keywords[:3]

    async with httpx.AsyncClient() as client:
        token = await _get_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": os.environ.get("REDDIT_USER_AGENT", "cast-bot/0.1"),
        }

        # Scan targeted subreddits
        for subreddit in subreddits:
            for keyword in keywords:
                resp = await client.get(
                    f"https://oauth.reddit.com/r/{subreddit}/search",
                    headers=headers,
                    params={"q": keyword, "sort": "new", "restrict_sr": "true", "limit": 8, "t": "week"},
                )
                if resp.status_code != 200:
                    continue
                for post in resp.json().get("data", {}).get("children", []):
                    d = post["data"]
                    if d.get("score", 0) < MIN_SCORE or d.get("num_comments", 0) < MIN_COMMENTS:
                        continue
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.reddit,
                        source_url=f"https://reddit.com{d['permalink']}",
                        source_title=d.get("title", ""),
                        source_body=(d.get("selftext") or d.get("url") or "")[:2000],
                    ))

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
