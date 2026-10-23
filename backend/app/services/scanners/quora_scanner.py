"""
Quora scanner — uses DuckDuckGo site:quora.com to surface questions in the
product's world. Quora blocks direct scraping so we go through DDG.
Queries and relevance vocabulary come from the product profile (SPEC §4.1).
"""
import httpx
from bs4 import BeautifulSoup
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.profile_intel import (
    derive_search_queries,
    get_relevance_signals,
    get_search_queries,
    is_blocked,
)
from app.core.proxy import proxy_kwargs

DDG_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_relevant(text: str, signals: list[str]) -> bool:
    t = text.lower()
    return any(s in t for s in signals)


async def scan_quora(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    queries = get_search_queries(product, "quora")
    if not queries:
        queries = [f"site:quora.com {q}" for q in derive_search_queries(product)]
    signals = get_relevance_signals(product, "quora")

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, **proxy_kwargs()) as client:
        for query in queries:
            try:
                resp = await client.post(DDG_URL, data={"q": query, "kl": "us-en"})
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for result in soup.select(".result")[:8]:
                    title_el = result.select_one(".result__title")
                    url_el = result.select_one(".result__url")
                    snippet_el = result.select_one(".result__snippet")

                    title = title_el.get_text(strip=True) if title_el else ""
                    url = url_el.get_text(strip=True) if url_el else ""
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    if "quora.com" not in url:
                        continue
                    if not title or not _is_relevant(title + " " + snippet, signals):
                        continue
                    if is_blocked(product, url):
                        continue
                    if not url.startswith("http"):
                        url = "https://" + url

                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.forum,
                        source_url=url,
                        source_title=title,
                        source_body=snippet[:2000],
                    ))
            except Exception:
                continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
