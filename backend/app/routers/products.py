from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.models.product_profile import ProductProfile, ProductProfileCreate, ProductProfileUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])
service = ProductService()


@router.post("/", response_model=ProductProfile)
async def create_product(data: ProductProfileCreate, user_id: UUID):
    return await service.create(user_id, data)


@router.get("/", response_model=list[ProductProfile])
async def list_products(user_id: UUID):
    return await service.list_for_user(user_id)


@router.get("/{product_id}", response_model=ProductProfile)
async def get_product(product_id: UUID, user_id: UUID):
    product = await service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductProfile)
async def update_product(product_id: UUID, data: ProductProfileUpdate, user_id: UUID):
    product = await service.update(product_id, user_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: UUID, user_id: UUID):
    deleted = await service.delete(product_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"deleted": True}
