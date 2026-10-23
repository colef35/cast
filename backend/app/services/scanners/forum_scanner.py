"""
Forum scanner — browses a product's target forum sections directly.
Forum search is usually blocked; browsing relevant sections beats it.
Sections, buying signals and relevance vocabulary come from the product
profile (SPEC §4.1) — a profile with no forum communities scans nothing.
"""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.profile_intel import (
    get_buying_signals,
    get_communities,
    get_relevance_signals,
)
from app.core.proxy import proxy_kwargs

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_relevant(text: str, required: list[str], buying_signals: list[str]) -> bool:
    t = text.lower()
    return any(s in t for s in required) and any(s in t for s in buying_signals)


async def scan_forums(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    sections = get_communities(product, "forum")
    if not sections:
        return opportunities

    buying_signals = [s.lower() for s in get_buying_signals(product)]
    required = get_relevance_signals(product, "forum")

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, **proxy_kwargs()) as client:
        for section_url in sections:
            try:
                resp = await client.get(section_url)
                if resp.status_code != 200:
                    continue

                host = urlparse(section_url)
                base = f"{host.scheme}://{host.netloc}"
                forum_name = host.netloc.replace("www.", "")

                soup = BeautifulSoup(resp.text, "html.parser")
                # XenForo 2 thread links use /threads/ path
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/threads/" not in href:
                        continue
                    text = a.get_text(strip=True)
                    if len(text) < 10:
                        continue
                    if not _is_relevant(text, required, buying_signals):
                        continue
                    if not href.startswith("http"):
                        href = base + href
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.forum,
                        source_url=href,
                        source_title=text[:200],
                        source_body=f"{forum_name} | {section_url.rstrip('/').split('/')[-1]}",
                    ))
            except Exception:
                continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
