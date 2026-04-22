"""
Forum scanner — scrapes contractor-specific forums for buying signal threads.
No API key required.
"""
import httpx
from bs4 import BeautifulSoup
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cast-bot/0.1)",
    "Accept-Language": "en-US,en;q=0.9",
}

# (forum_name, search_url_template)
FORUMS = [
    ("contractortalk", "https://www.contractortalk.com/search/?q={query}&o=date"),
    ("thefasteners", "https://www.thefasteners.com/search/?q={query}"),
    ("excavationcontractor", "https://www.excavationcontractortalk.com/search/?q={query}&o=date"),
]

SEARCH_TERMS = [
    "construction software",
    "job costing software",
    "contractor app",
    "procore alternative",
    "scheduling software",
    "payroll software contractor",
]


async def scan_forums(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    buying_signals = DATUM_PROFILE["buying_signals"]

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        for forum_name, url_template in FORUMS:
            for term in SEARCH_TERMS:
                try:
                    url = url_template.format(query=term.replace(" ", "+"))
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Generic thread link extraction — works across most XenForo/vBulletin forums
                    for link in soup.select("a[href]")[:40]:
                        href = link.get("href", "")
                        text = link.get_text(strip=True)

                        if not text or len(text) < 15:
                            continue
                        if not any(sig in text.lower() for sig in buying_signals):
                            continue
                        if not href.startswith("http"):
                            base = url_template.split("/search")[0]
                            href = base + href

                        opportunities.append(OpportunityCreate(
                            product_id=product.id,
                            user_id=product.user_id,
                            channel=Channel.forum,
                            source_url=href,
                            source_title=text[:200],
                            source_body=f"From {forum_name} — search: {term}",
                        ))
                except Exception:
                    continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
