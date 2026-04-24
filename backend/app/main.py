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


@app.get("/debug/hn-post")
async def debug_hn_post():
    """Test posting a comment to the HN front page newest thread."""
    import httpx
    from bs4 import BeautifulSoup
    from app.services.hn_poster import post_comment, _cookie
    try:
        # Find a recent thread to test with
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://hacker-news.firebaseio.com/v0/newstories.json")
            ids = r.json()[:5]
        # Use first story ID
        thread_url = f"https://news.ycombinator.com/item?id={ids[0]}"
        url = await post_comment(
            thread_url,
            "Test — ignore. Construction management software for contractors: https://lowlevellogic.org"
        )
        if url is None:
            return {"status": "skipped", "reason": "Thread has no comment form (too old or closed)", "thread": thread_url}
        return {"status": "ok", "url": url}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/config")
def config():
    """Shows which posting channels are configured."""
    import os
    return {
        "hackernews": bool(os.environ.get("HN_COOKIE")),
        "reddit": bool(os.environ.get("REDDIT_USERNAME")),
        "youtube": bool(os.environ.get("YOUTUBE_REFRESH_TOKEN")),
        "proxy": bool(os.environ.get("CAST_PROXY")),
        "ai_drafts": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


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
