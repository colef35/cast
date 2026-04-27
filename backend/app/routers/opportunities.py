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


@router.get("/all", response_model=list[Opportunity])
async def list_all(user_id: UUID, status: str = None):
    return await service.list_by_status(user_id, status)


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

    await _post_opp(result.data)
    return await service.set_status(opp_id, user_id, OpportunityStatus.sent)


@router.post("/send-approved", response_model=dict)
async def send_approved(user_id: UUID):
    """Send all approved opportunities in the background."""
    asyncio.create_task(_run_send_approved(str(user_id)))
    return {"status": "started"}


async def _run_send_approved(user_id: str):
    import logging
    log = logging.getLogger("send_approved")
    from app.core.supabase import get_supabase
    db = get_supabase()
    result = (
        db.table("opportunities")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", OpportunityStatus.approved)
        .execute()
    )
    opps = result.data or []
    log.warning(f"[send_approved] {len(opps)} approved opportunities to post")
    sent = 0
    for opp in opps:
        await asyncio.sleep(4)
        try:
            posted = await _post_opp(opp)
            if posted:
                from uuid import UUID
                await service.set_status(UUID(opp["id"]), UUID(user_id), OpportunityStatus.sent)
                sent += 1
        except Exception as e:
            log.warning(f"[send_approved] FAILED {opp['source_url'][:60]}: {e}")
    log.warning(f"[send_approved] Done — posted {sent}/{len(opps)}")


async def _post_opp(opp: dict) -> bool:
    channel = opp.get("channel", "")
    draft = opp.get("draft", "")
    source_url = opp.get("source_url", "")

    if not draft or not source_url:
        return False

    if channel == "hackernews":
        from app.services.hn_poster import post_comment
        result = await post_comment(source_url, draft)
        return result is not None

    if channel == "reddit":
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

    if channel == "forum":
        import os
        if not os.environ.get("CT_USERNAME"):
            return False
        from app.services.forum_poster import post_reply
        result = await post_reply(source_url, draft)
        return result is not None

    return False
