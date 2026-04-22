from uuid import UUID
from app.models.opportunity import Opportunity, OpportunityCreate, OpportunityStatus
from app.services.scorer import score_and_draft
from app.services.product_service import ProductService
from app.core.supabase import get_supabase

TABLE = "opportunities"


class OpportunityService:
    def __init__(self):
        self.db = get_supabase()
        self.products = ProductService()

    async def ingest(self, opp: OpportunityCreate) -> Opportunity:
        product = await self.products.get(opp.product_id, opp.user_id)
        if not product:
            raise ValueError("Product not found")

        relevance, roi, draft = score_and_draft(product, opp)

        row = {
            **opp.model_dump(),
            "product_id": str(opp.product_id),
            "user_id": str(opp.user_id),
            "relevance_score": relevance,
            "roi_score": roi,
            "draft": draft,
            "status": OpportunityStatus.pending,
        }
        result = self.db.table(TABLE).insert(row).execute()
        return Opportunity(**result.data[0])

    async def list_pending(self, user_id: UUID) -> list[Opportunity]:
        result = (
            self.db.table(TABLE)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("status", OpportunityStatus.pending)
            .order("roi_score", desc=True)
            .execute()
        )
        return [Opportunity(**r) for r in result.data]

    async def set_status(self, opp_id: UUID, user_id: UUID, status: OpportunityStatus) -> Opportunity | None:
        from datetime import datetime
        updates = {"status": status}
        if status in (OpportunityStatus.approved, OpportunityStatus.rejected, OpportunityStatus.sent):
            updates["acted_at"] = datetime.utcnow().isoformat()

        result = (
            self.db.table(TABLE)
            .update(updates)
            .eq("id", str(opp_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return Opportunity(**result.data[0]) if result.data else None
