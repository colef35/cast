from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.routers import products, opportunities, scan, billing, auth
from app.routers.user_auth import router as user_auth_router
from app.core.database import init_db
import asyncio
import os


async def _auto_scan_loop():
    await asyncio.sleep(60)
    while True:
        try:
            from app.core.supabase import get_supabase
            from app.services.product_service import ProductService
            from app.services.opportunity_service import OpportunityService
            from app.services.scanners.hn_scanner import scan_hn
            from app.services.scanners.reddit_scanner import scan_reddit
            from app.services.scanners.web_scanner import scan_web
            from app.services.scanners.youtube_scanner import scan_youtube
            from app.services.scanners.forum_scanner import scan_forums

            db = get_supabase()
            products_data = db.table("product_profiles").select("*").execute().data or []

            opp_service = OpportunityService()
            for p_row in products_data:
                from app.models.product_profile import ProductProfile
                try:
                    product = ProductProfile(**p_row)
                except Exception:
                    continue
                raw_lists = await asyncio.gather(
                    scan_hn(product),
                    scan_reddit(product),
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
        await asyncio.sleep(2 * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(_auto_scan_loop())
    yield


app = FastAPI(title="CAST API", version="0.1.0", lifespan=lifespan)

app.include_router(user_auth_router)
app.include_router(products.router)
app.include_router(opportunities.router)
app.include_router(scan.router)
app.include_router(billing.router)
app.include_router(auth.router)

_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
def dashboard():
    index = os.path.join(_static_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"name": "CAST API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {
        "hackernews": bool(os.environ.get("HN_COOKIE")),
        "reddit": bool(os.environ.get("REDDIT_USERNAME")),
        "youtube": bool(os.environ.get("YOUTUBE_REFRESH_TOKEN")),
        "ai_drafts": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


@app.get("/stats")
def stats(user_id: str = None):
    from app.core.supabase import get_supabase
    from datetime import datetime, timedelta
    db = get_supabase()

    q = db.table("opportunities").select("channel, status, created_at")
    if user_id:
        q = q.eq("user_id", user_id)
    opps = q.execute().data or []

    subs = db.table("subscriptions").select("plan, active, created_at").execute().data or []

    now = datetime.utcnow()
    last_24h = [o for o in opps if o.get("created_at", "") >= (now - timedelta(hours=24)).isoformat()]

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
            "by_channel": by_channel,
            "pending": sum(1 for o in opps if o.get("status") == "pending"),
            "approved": sum(1 for o in opps if o.get("status") == "approved"),
            "sent": sum(1 for o in opps if o.get("status") == "sent"),
            "rejected": sum(1 for o in opps if o.get("status") == "rejected"),
        },
        "subscribers": {
            "total_active": len(active_subs),
            "by_plan": by_plan,
        },
    }


@app.post("/admin/migrate-user")
def migrate_user(from_id: str, to_id: str, secret: str = ""):
    if secret != os.environ.get("CRON_SECRET", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    from app.core.database import get_db
    conn = get_db()
    r1 = conn.execute("UPDATE opportunities SET user_id=? WHERE user_id=?", [to_id, from_id])
    r2 = conn.execute("UPDATE product_profiles SET user_id=? WHERE user_id=?", [to_id, from_id])
    conn.commit()
    conn.close()
    return {"opportunities_migrated": r1.rowcount, "products_migrated": r2.rowcount}
