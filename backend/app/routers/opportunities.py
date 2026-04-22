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
