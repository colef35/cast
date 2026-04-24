from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.services.scanners.hn_scanner import scan_hn
from app.services.scanners.reddit_scanner import scan_reddit
from app.services.scanners.web_scanner import scan_web
from app.services.scanners.youtube_scanner import scan_youtube
from app.services.scanners.forum_scanner import scan_forums
from app.services.opportunity_service import OpportunityService
from app.services.product_service import ProductService
from app.models.opportunity import Opportunity

router = APIRouter(prefix="/scan", tags=["scan"])
opp_service = OpportunityService()
product_service = ProductService()


@router.post("/hn/{product_id}", response_model=list[Opportunity])
async def scan_hackernews(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    raw = await scan_hn(product)
    results = []
    for opp_create in raw:
        opp = await opp_service.ingest(opp_create)
        results.append(opp)

    return results


@router.post("/reddit/{product_id}", response_model=list[Opportunity])
async def scan_reddit_endpoint(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    raw = await scan_reddit(product)
    results = []
    for opp_create in raw:
        opp = await opp_service.ingest(opp_create)
        results.append(opp)

    return results


@router.post("/web/{product_id}", response_model=list[Opportunity])
async def scan_web_endpoint(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    results = []
    for opp_create in await scan_web(product):
        results.append(await opp_service.ingest(opp_create))
    return results


@router.post("/youtube/{product_id}", response_model=list[Opportunity])
async def scan_youtube_endpoint(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    results = []
    for opp_create in await scan_youtube(product):
        results.append(await opp_service.ingest(opp_create))
    return results


@router.post("/forums/{product_id}", response_model=list[Opportunity])
async def scan_forums_endpoint(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    results = []
    for opp_create in await scan_forums(product):
        results.append(await opp_service.ingest(opp_create))
    return results


@router.delete("/purge-old", response_model=dict)
async def purge_old_leads(user_id: UUID, days: int = 30):
    """Delete pending HN leads that point to old threads (item ID below cutoff)."""
    from app.core.supabase import get_supabase
    import re
    import time
    db = get_supabase()
    # HN item IDs grow at ~500/hour. Estimate ID cutoff for N days ago.
    # Current top items are ~47.9M. 30 days * 24h * ~500/h ≈ 360000 items ago.
    current_id = 47_900_000
    cutoff_id = current_id - (days * 24 * 500)
    rows = (
        db.table("opportunities")
        .select("id,source_url")
        .eq("user_id", str(user_id))
        .eq("status", "pending")
        .eq("channel", "hackernews")
        .execute()
    ).data or []
    deleted = 0
    for row in rows:
        url = row.get("source_url", "")
        m = re.search(r"id=(\d+)", url)
        if m and int(m.group(1)) < cutoff_id:
            db.table("opportunities").delete().eq("id", row["id"]).execute()
            deleted += 1
    return {"deleted": deleted, "cutoff_id": cutoff_id, "total_checked": len(rows)}


@router.post("/all/{product_id}", response_model=list[Opportunity])
async def scan_all(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from asyncio import gather
    hn_raw, reddit_raw, web_raw, yt_raw, forum_raw = await gather(
        scan_hn(product),
        scan_reddit(product),
        scan_web(product),
        scan_youtube(product),
        scan_forums(product),
    )

    results = []
    for opp_create in hn_raw + reddit_raw + web_raw + yt_raw + forum_raw:
        results.append(await opp_service.ingest(opp_create))
    return results
