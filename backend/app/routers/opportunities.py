from fastapi import APIRouter, HTTPException
from uuid import UUID
import asyncio
from app.models.opportunity import Opportunity, OpportunityCreate, OpportunityStatus
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])
service = OpportunityService()


@router.post("/", response_model=Opportunity)
async def ingest_opportunity(data: OpportunityCreate):
    return await service.ingest(data)


@router.get("/pending", response_model=list[Opportunity])
async def list_pending(user_id: UUID):
    return await service.list_pending(user_id)


@router.patch("/{opp_id}/approve", response_model=Opportunity)
async def approve(opp_id: UUID, user_id: UUID):
    opp = await service.set_status(opp_id, user_id, OpportunityStatus.approved)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.patch("/{opp_id}/reject", response_model=Opportunity)
async def reject(opp_id: UUID, user_id: UUID):
    opp = await service.set_status(opp_id, user_id, OpportunityStatus.rejected)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.patch("/{opp_id}/send", response_model=Opportunity)
async def send(opp_id: UUID, user_id: UUID):
    from app.core.supabase import get_supabase
    db = get_supabase()
    result = db.table("opportunities").select("*").eq("id", str(opp_id)).eq("user_id", str(user_id)).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = result.data
    await _post_opp(opp)
    return await service.set_status(opp_id, user_id, OpportunityStatus.sent)


@router.post("/send-all", response_model=dict)
async def send_all(user_id: UUID):
    """Fire-and-forget: kicks off background sending, returns immediately."""
    asyncio.create_task(_run_send_all(str(user_id)))
    return {"status": "started", "message": "Sending in background — check /stats for progress"}


async def _run_send_all(user_id: str):
    import logging
    log = logging.getLogger("send_all")
    from app.core.supabase import get_supabase
    db = get_supabase()
    result = (
        db.table("opportunities")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "pending")
        .execute()
    )

    import os
    opps = result.data or []
    yt_enabled = bool(os.environ.get("YOUTUBE_REFRESH_TOKEN"))
    # Filter to channels we can actually post to
    postable = [o for o in opps if
        o.get("draft") and o.get("source_url") and
        (o.get("channel") == "hackernews" or
         (o.get("channel") == "youtube" and yt_enabled))
    ]
    log.warning(f"[send_all] Starting — {len(postable)} postable (of {len(opps)} total)")
    sent = 0
    for opp in postable:
        await asyncio.sleep(4)
        try:
            posted = await _post_opp(opp)
            if posted:
                from uuid import UUID
                await service.set_status(UUID(opp["id"]), UUID(user_id), OpportunityStatus.sent)
                sent += 1
                log.warning(f"[send_all] Sent {sent}: {opp['source_url'][:60]}")
            else:
                log.warning(f"[send_all] Skipped (no poster): channel={opp.get('channel')} url={opp['source_url'][:60]}")
        except Exception as e:
            log.warning(f"[send_all] FAILED {opp['source_url'][:60]}: {e}")


async def _post_opp(opp: dict) -> bool:
    """Post to the appropriate platform based on channel. Returns True if posted."""
    channel = opp.get("channel", "")
    draft = opp.get("draft", "")
    source_url = opp.get("source_url", "")

    if not draft or not source_url:
        return False

    if channel == "hackernews":
        from app.services.hn_poster import post_comment
        result = await post_comment(source_url, draft)
        return result is not None  # None means thread too old, skip

    if channel == "reddit":
        import os
        if not os.environ.get("REDDIT_USERNAME"):
            return False
        from app.services.reddit_poster import post_comment
        await post_comment(source_url, draft)
        return True

    if channel == "youtube":
        import os
        if not os.environ.get("YOUTUBE_REFRESH_TOKEN"):
            return False
        from app.services.youtube_poster import post_comment as yt_post
        result = await yt_post(source_url, draft)
        return result is not None

    # Forum — no posting capability yet, skip
    return False
