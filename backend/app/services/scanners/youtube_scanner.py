"""
YouTube scanner — finds construction software videos and surfaces them as
reply opportunities. Uses YouTube's public search page (no API key).
"""
import httpx
import json
import re
from app.models.opportunity import Channel, OpportunityCreate
from app.models.product_profile import ProductProfile
from app.services.datum_profile import DATUM_PROFILE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cast-bot/0.1)",
    "Accept-Language": "en-US,en;q=0.9",
}

SEARCH_QUERIES = [
    "construction management software review",
    "procore alternative 2024",
    "best construction software for small contractors",
    "construction job costing software",
    "contractor management app review",
    "construction scheduling software",
]


def _extract_videos(html: str) -> list[dict]:
    match = re.search(r"var ytInitialData = ({.*?});</script>", html, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
        contents = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )
        videos = []
        for section in contents:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                vr = item.get("videoRenderer")
                if not vr:
                    continue
                vid_id = vr.get("videoId")
                title = "".join(
                    r.get("text", "") for r in
                    vr.get("title", {}).get("runs", [])
                )
                snippet = "".join(
                    r.get("text", "") for r in
                    vr.get("descriptionSnippet", {}).get("runs", [])
                )
                if vid_id and title:
                    videos.append({"id": vid_id, "title": title, "snippet": snippet})
        return videos
    except Exception:
        return []


async def scan_youtube(product: ProductProfile) -> list[OpportunityCreate]:
    opportunities = []
    buying_signals = DATUM_PROFILE["buying_signals"]

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        for query in SEARCH_QUERIES:
            try:
                resp = await client.get(
                    "https://www.youtube.com/results",
                    params={"search_query": query}
                )
                if resp.status_code != 200:
                    continue

                for video in _extract_videos(resp.text)[:5]:
                    combined = (video["title"] + " " + video["snippet"]).lower()
                    if not any(sig in combined for sig in buying_signals):
                        continue

                    opportunities.append(OpportunityCreate(
                        product_id=product.id,
                        user_id=product.user_id,
                        channel=Channel.youtube,
                        source_url=f"https://www.youtube.com/watch?v={video['id']}",
                        source_title=video["title"],
                        source_body=video["snippet"][:2000],
                    ))
            except Exception:
                continue

    seen, deduped = set(), []
    for o in opportunities:
        if o.source_url not in seen:
            seen.add(o.source_url)
            deduped.append(o)
    return deduped
