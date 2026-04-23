from fastapi import APIRouter, HTTPException
from uuid import UUID
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
    import os
    from app.core.supabase import get_supabase

    db = get_supabase()
    result = db.table("opportunities").select("*").eq("id", str(opp_id)).eq("user_id", str(user_id)).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = result.data
    channel = opp.get("channel")
    draft = opp.get("draft", "")
    source_url = opp.get("source_url", "")

    if channel == "reddit" and os.environ.get("REDDIT_USERNAME") and draft:
        try:
            from app.services.reddit_poster import post_comment
            await post_comment(source_url, draft)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Reddit post failed: {e}")

    updated = await service.set_status(opp_id, user_id, OpportunityStatus.sent)
    return updated


@router.post("/send-all", response_model=dict)
async def send_all_approved(user_id: UUID):
    """Send all approved Reddit opportunities automatically."""
    import os
    from app.core.supabase import get_supabase
    from app.services.reddit_poster import post_comment

    if not os.environ.get("REDDIT_USERNAME"):
        raise HTTPException(status_code=503, detail="Reddit credentials not configured")

    db = get_supabase()
    result = (
        db.table("opportunities")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("status", "pending")
        .eq("channel", "reddit")
        .execute()
    )

    sent, failed = 0, 0
    for opp in (result.data or []):
        draft = opp.get("draft", "")
        source_url = opp.get("source_url", "")
        if not draft or not source_url:
            continue
        try:
            await post_comment(source_url, draft)
            await service.set_status(opp["id"], user_id, OpportunityStatus.sent)
            sent += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed}
