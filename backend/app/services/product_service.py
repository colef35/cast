from uuid import UUID
from datetime import datetime
from app.models.product_profile import ProductProfile, ProductProfileCreate, ProductProfileUpdate
from app.core.supabase import get_supabase

TABLE = "product_profiles"


class ProductService:
    def __init__(self):
        self.db = get_supabase()

    async def create(self, user_id: UUID, data: ProductProfileCreate) -> ProductProfile:
        row = {"user_id": str(user_id), **data.model_dump()}
        result = self.db.table(TABLE).insert(row).execute()
        return ProductProfile(**result.data[0])

    async def list_for_user(self, user_id: UUID) -> list[ProductProfile]:
        result = self.db.table(TABLE).select("*").eq("user_id", str(user_id)).execute()
        return [ProductProfile(**r) for r in result.data]

    async def get(self, product_id: UUID, user_id: UUID) -> ProductProfile | None:
        result = (
            self.db.table(TABLE)
            .select("*")
            .eq("id", str(product_id))
            .eq("user_id", str(user_id))
            .single()
            .execute()
        )
        return ProductProfile(**result.data) if result.data else None

    async def update(self, product_id: UUID, user_id: UUID, data: ProductProfileUpdate) -> ProductProfile | None:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = (
            self.db.table(TABLE)
            .update(updates)
            .eq("id", str(product_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return ProductProfile(**result.data[0]) if result.data else None

    async def delete(self, product_id: UUID, user_id: UUID) -> bool:
        result = (
            self.db.table(TABLE)
            .delete()
            .eq("id", str(product_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return len(result.data) > 0
