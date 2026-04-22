"""
Web scanner — searches DuckDuckGo for buying-signal posts across the internet.
No API key required.
"""
import httpx
from bs4 import BeautifulSoup
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

DDG_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cast-bot/0.1)",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_QUERIES = [
    "alternative to procore construction software",
    "construction management software too expensive",
    "best construction job costing software small contractor",
    "procore alternative affordable",
    "contractor software recommendation site:reddit.com OR site:contractortalk.com OR site:forum",
    "construction payroll software recommendation",
    "bid management software for contractors",
    "construction scheduling software small business",
    "what construction software do you use",
    "DATUM+ construction software review",
    "lowlevellogic.org construction",
]


async def scan_web(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    buying_signals = DATUM_PROFILE["buying_signals"]

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        for query in SEARCH_QUERIES:
            try:
                resp = await client.post(DDG_URL, data={"q": query, "kl": "us-en"})
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for result in soup.select(".result")[:6]:
                    title_el = result.select_one(".result__title")
                    url_el = result.select_one(".result__url")
                    snippet_el = result.select_one(".result__snippet")

                    title = title_el.get_text(strip=True) if title_el else ""
                    url = url_el.get_text(strip=True) if url_el else ""
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    if not url or not title:
                        continue

                    # Normalize URL
                    if not url.startswith("http"):
                        url = "https://" + url

                    # Only surface results with buying signals
                    combined = (title + " " + snippet).lower()
                    if not any(sig in combined for sig in buying_signals):
                        continue

                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.web,
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
