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
    """Send all pending opportunities across all channels."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    result = (
        db.table("opportunities")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("status", "pending")
        .execute()
    )

    sent, failed, skipped = 0, 0, 0
    for opp in (result.data or []):
        if not opp.get("draft") or not opp.get("source_url"):
            skipped += 1
            continue
        # Rate limit — don't hammer platforms
        await asyncio.sleep(3)
        try:
            posted = await _post_opp(opp)
            if posted:
                await service.set_status(opp["id"], user_id, OpportunityStatus.sent)
                sent += 1
            else:
                skipped += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "skipped": skipped}


async def _post_opp(opp: dict) -> bool:
    """Post to the appropriate platform based on channel. Returns True if posted."""
    channel = opp.get("channel", "")
    draft = opp.get("draft", "")
    source_url = opp.get("source_url", "")

    if not draft or not source_url:
        return False

    if channel == "hackernews":
        from app.services.hn_poster import post_comment
        await post_comment(source_url, draft)
        return True

    if channel == "reddit":
        import os
        if not os.environ.get("REDDIT_USERNAME"):
            return False
        from app.services.reddit_poster import post_comment
        await post_comment(source_url, draft)
        return True

    # YouTube and forum — no posting capability yet, skip
    return False
