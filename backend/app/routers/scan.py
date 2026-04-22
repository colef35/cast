from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.services.scanners.hn_scanner import scan_hn
from app.services.scanners.reddit_scanner import scan_reddit
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


@router.post("/all/{product_id}", response_model=list[Opportunity])
async def scan_all(product_id: UUID, user_id: UUID):
    product = await product_service.get(product_id, user_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from asyncio import gather
    hn_raw, reddit_raw = await gather(scan_hn(product), scan_reddit(product))

    results = []
    for opp_create in hn_raw + reddit_raw:
        opp = await opp_service.ingest(opp_create)
        results.append(opp)

    return results
