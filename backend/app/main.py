from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import products, opportunities, scan, billing
from app.core.database import init_db
import asyncio


async def _auto_scan_loop():
    """Runs a full scan every 6 hours automatically."""
    await asyncio.sleep(60)  # wait 1 min after startup before first scan
    while True:
        try:
            from app.core.supabase import get_supabase
            from app.services.product_service import ProductService
            from app.services.opportunity_service import OpportunityService
            from app.services.scanners.hn_scanner import scan_hn
            from app.services.scanners.web_scanner import scan_web
            from app.services.scanners.youtube_scanner import scan_youtube
            from app.services.scanners.forum_scanner import scan_forums

            db = get_supabase()
            products_data = db.table("product_profiles").select("*").execute().data or []

            opp_service = OpportunityService()
            for p_row in products_data:
                from app.models.product_profile import ProductProfile
                product = ProductProfile(**p_row)
                raw_lists = await asyncio.gather(
                    scan_hn(product),
                    scan_web(product),
                    scan_youtube(product),
                    scan_forums(product),
                    return_exceptions=True,
                )
                for raw in raw_lists:
                    if isinstance(raw, Exception):
                        continue
                    for opp_create in raw:
                        try:
                            await opp_service.ingest(opp_create)
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(6 * 3600)  # run every 6 hours


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(_auto_scan_loop())
    yield


app = FastAPI(title="CAST API", version="0.1.0", lifespan=lifespan)

app.include_router(products.router)
app.include_router(opportunities.router)
app.include_router(scan.router)
app.include_router(billing.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    from app.core.supabase import get_supabase
    from datetime import datetime, timedelta
    db = get_supabase()

    opps = db.table("opportunities").select("channel, status, created_at").execute().data or []
    subs = db.table("subscriptions").select("plan, active, created_at").execute().data or []

    now = datetime.utcnow()
    last_24h = [o for o in opps if o.get("created_at", "") >= (now - timedelta(hours=24)).isoformat()]
    last_7d  = [o for o in opps if o.get("created_at", "") >= (now - timedelta(days=7)).isoformat()]

    by_channel = {}
    for o in opps:
        ch = o.get("channel", "unknown")
        by_channel[ch] = by_channel.get(ch, 0) + 1

    active_subs = [s for s in subs if s.get("active")]
    by_plan = {}
    for s in active_subs:
        p = s.get("plan", "unknown")
        by_plan[p] = by_plan.get(p, 0) + 1

    return {
        "opportunities": {
            "total": len(opps),
            "last_24h": len(last_24h),
            "last_7d": len(last_7d),
            "by_channel": by_channel,
            "pending": sum(1 for o in opps if o.get("status") == "pending"),
            "sent": sum(1 for o in opps if o.get("status") == "sent"),
        },
        "subscribers": {
            "total_active": len(active_subs),
            "by_plan": by_plan,
        },
    }
