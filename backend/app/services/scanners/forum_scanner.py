"""
Forum scanner — finds construction contractor threads worth replying to.
Targets XenForo-based contractor forums.
"""
import httpx
from bs4 import BeautifulSoup
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE
from app.core.proxy import proxy_kwargs

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

FORUMS = [
    ("contractortalk", "https://www.contractortalk.com/search/", {"q": "{query}", "o": "date"}),
    ("excavationcontractor", "https://www.excavationcontractortalk.com/search/", {"q": "{query}", "o": "date"}),
    ("theconstructionforum", "https://www.theconstructionforum.org/search.php", {"keywords": "{query}", "searchdate": "1"}),
]

SEARCH_TERMS = [
    "construction software",
    "job costing",
    "procore alternative",
    "contractor app",
    "scheduling software",
    "payroll software",
    "bid management",
]

BUYING_SIGNALS = DATUM_PROFILE["buying_signals"]

CONSTRUCTION_REQUIRED = [
    "construction", "contractor", "excavat", "grading", "job cost", "procore",
    "buildertrend", "subcontract", "site work", "paving", "concrete", "estimat",
    "bid", "change order", "payroll", "scheduling", "field management",
]


def _is_relevant(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in CONSTRUCTION_REQUIRED) and any(s in t for s in BUYING_SIGNALS)


async def scan_forums(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, **proxy_kwargs()) as client:
        for forum_name, base_url, param_template in FORUMS:
            for term in SEARCH_TERMS:
                try:
                    params = {k: v.format(query=term.replace(" ", "+")) for k, v in param_template.items()}
                    resp = await client.get(base_url, params=params)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    base_domain = base_url.split("/search")[0]

                    # XenForo thread links
                    for link in soup.select("h3 a, .title a, .thread-title a, h4 a")[:30]:
                        href = link.get("href", "")
                        text = link.get_text(strip=True)
                        if len(text) < 10:
                            continue
                        if not _is_relevant(text):
                            continue
                        if not href.startswith("http"):
                            href = base_domain + "/" + href.lstrip("/")
                        opportunities.append(OpportunityCreate(
                            product_id=product.id,
                            user_id=product.user_id,
                            channel=Channel.forum,
                            source_url=href,
                            source_title=text[:200],
                            source_body=f"Forum: {forum_name} | Search: {term}",
                        ))
                except Exception:
                    continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
