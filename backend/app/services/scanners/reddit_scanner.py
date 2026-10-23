import os
import httpx
import xml.etree.ElementTree as ET
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.profile_intel import get_buying_signals, get_communities

UA = os.environ.get("CAST_USER_AGENT", "CAST/0.1 by Low Level Logic (marketing listener)")
MAX_POSTS = 5


async def _scan_rss(client: httpx.AsyncClient, subreddit: str, seen: set) -> list[dict]:
    """Scan a subreddit via RSS — no auth needed, works from any IP."""
    try:
        resp = await client.get(
            f"https://www.reddit.com/r/{subreddit}/new.rss",
            headers={"User-Agent": UA},
        )
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        posts = []
        for entry in root.findall("atom:entry", ns)[:MAX_POSTS]:
            link = entry.find("atom:link", ns)
            title = entry.find("atom:title", ns)
            content = entry.find("atom:content", ns)
            url = link.attrib.get("href", "") if link is not None else ""
            if not url or url in seen:
                continue
            seen.add(url)
            posts.append({
                "url": url,
                "title": (title.text or "") if title is not None else "",
                "body": (content.text or "")[:2000] if content is not None else "",
            })
        return posts
    except Exception:
        return []


async def _search_json(client: httpx.AsyncClient, subreddit: str, keyword: str, seen: set) -> list[dict]:
    """Search subreddit via JSON API — may be blocked from datacenter IPs."""
    try:
        resp = await client.get(
            f"https://www.reddit.com/r/{subreddit}/search.json",
            params={"q": keyword, "sort": "new", "restrict_sr": "true", "limit": 10, "t": "month"},
            headers={"User-Agent": UA},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        posts = []
        for post in resp.json().get("data", {}).get("children", []):
            d = post["data"]
            if d.get("score", 0) < 1:
                continue
            url = f"https://reddit.com{d['permalink']}"
            if url in seen:
                continue
            seen.add(url)
            posts.append({
                "url": url,
                "title": d.get("title", ""),
                "body": (d.get("selftext") or "")[:2000],
            })
        return posts
    except Exception:
        return []


async def scan_reddit(product: ProductProfile) -> list[OpportunityCreate]:
    # All product specifics come from the profile (SPEC §4.1): target
    # subreddits, keywords, buying signals. No communities configured →
    # keyword search across all of Reddit instead of an RSS sweep.
    subreddits = get_communities(product, "reddit")
    keywords = product.keywords[:4] if product.keywords else product.problem_phrases[:4]
    keywords = [kw.lower() for kw in keywords]
    buying_signals = {s.lower() for s in get_buying_signals(product)}

    opportunities = []
    seen: set = set()

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        # Primary: RSS scan per subreddit (bypasses IP blocks)
        for subreddit in subreddits[:12]:
            posts = await _scan_rss(client, subreddit, seen)
            for p in posts:
                # Filter by buying signals or keywords
                combined = (p["title"] + " " + p["body"]).lower()
                if any(sig in combined for sig in buying_signals) or any(kw in combined for kw in keywords):
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.reddit,
                        source_url=p["url"],
                        source_title=p["title"],
                        source_body=p["body"],
                    ))

        # Secondary: search API per keyword (best-effort, may be blocked).
        # With no configured subreddits, search r/all by keyword.
        search_targets = subreddits[:6] if subreddits else ["all"]
        for subreddit in search_targets:
            for keyword in keywords[:2]:
                posts = await _search_json(client, subreddit, keyword, seen)
                for p in posts:
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.reddit,
                        source_url=p["url"],
                        source_title=p["title"],
                        source_body=p["body"],
                    ))

    # Final dedup
    final_seen: set = set()
    deduped = []
    for o in opportunities:
        if o.source_url not in final_seen:
            final_seen.add(o.source_url)
            deduped.append(o)
    return deduped
