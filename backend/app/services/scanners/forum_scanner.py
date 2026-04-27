"""
Forum scanner — browses construction contractor forums by section.
ContractorTalk search is blocked; we browse relevant subforums directly instead.
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

# Browse these sections directly — highest signal-to-noise for DATUM+
CONTRACTORTALK_SECTIONS = [
    "https://www.contractortalk.com/forums/accounting-software-discussion.108/",
    "https://www.contractortalk.com/forums/business.16/",
    "https://www.contractortalk.com/forums/construction.4/",
    "https://www.contractortalk.com/forums/commercial-construction.84/",
    "https://www.contractortalk.com/forums/excavation.71/",
    "https://www.contractortalk.com/forums/general-discussion.2/",
]

BUYING_SIGNALS = DATUM_PROFILE["buying_signals"]
CONSTRUCTION_REQUIRED = [
    "construction", "contractor", "excavat", "grading", "job cost", "procore",
    "buildertrend", "subcontract", "site work", "paving", "concrete", "estimat",
    "bid", "change order", "payroll", "scheduling", "field management",
    "software", "app", "tool", "manage", "track", "recommend",
]


def _is_relevant(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in CONSTRUCTION_REQUIRED) and any(s in t for s in BUYING_SIGNALS)


async def scan_forums(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, **proxy_kwargs()) as client:
        for section_url in CONTRACTORTALK_SECTIONS:
            try:
                resp = await client.get(section_url)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                # XenForo 2 thread links use /threads/ path
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/threads/" not in href:
                        continue
                    text = a.get_text(strip=True)
                    if len(text) < 10:
                        continue
                    if not _is_relevant(text):
                        continue
                    if not href.startswith("http"):
                        href = "https://www.contractortalk.com" + href
                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.forum,
                        source_url=href,
                        source_title=text[:200],
                        source_body=f"ContractorTalk | {section_url.split('/')[-2]}",
                    ))
            except Exception:
                continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
