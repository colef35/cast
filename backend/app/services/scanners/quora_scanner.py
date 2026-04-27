"""
Quora scanner — uses DuckDuckGo site:quora.com to surface construction software
questions. Quora blocks direct scraping so we go through DDG.
"""
import httpx
from bs4 import BeautifulSoup
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE
from app.core.proxy import proxy_kwargs

DDG_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
    "site:quora.com procore alternative construction",
    "site:quora.com best construction management software small contractor",
    "site:quora.com construction job costing software",
    "site:quora.com construction scheduling software recommendation",
    "site:quora.com contractor software recommendation",
    "site:quora.com buildertrend alternative",
    "site:quora.com construction payroll software",
    "site:quora.com construction app contractor",
]

BUYING_SIGNALS = DATUM_PROFILE["buying_signals"]
CONSTRUCTION_SIGNALS = [
    "construction", "contractor", "procore", "buildertrend", "job cost",
    "payroll", "scheduling", "bid", "excavat", "subcontract",
]


def _is_relevant(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in CONSTRUCTION_SIGNALS)


async def scan_quora(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, **proxy_kwargs()) as client:
        for query in QUERIES:
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
                    if not title or not _is_relevant(title + " " + snippet):
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
