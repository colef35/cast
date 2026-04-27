from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.routers import products, opportunities, scan, billing, auth
from app.routers.user_auth import router as user_auth_router
from app.core.database import init_db
import asyncio
import os


AUTO_APPROVE_THRESHOLD = 0.55  # roi_score >= this → auto-approve and post


async def _auto_post_pending(user_id: str):
    """Auto-approve and post high-scoring pending opportunities for a user."""
    import logging
    log = logging.getLogger("cast.auto_post")
    from app.core.supabase import get_supabase
    from app.models.opportunity import OpportunityStatus
    from app.routers.opportunities import _post_opp
    from uuid import UUID

    db = get_supabase()
    result = (
        db.table("opportunities")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", OpportunityStatus.pending)
        .execute()
    )
    pending = result.data or []
    candidates = [o for o in pending if (o.get("roi_score") or 0) >= AUTO_APPROVE_THRESHOLD]
    log.warning(f"[auto_post] {len(candidates)}/{len(pending)} pending meet threshold for user {user_id[:8]}")

    sent = 0
    for opp in candidates:
        await asyncio.sleep(5)
        try:
            posted = await _post_opp(opp)
            if posted:
                db.table("opportunities").update({
                    "status": OpportunityStatus.sent,
                    "acted_at": __import__("datetime").datetime.utcnow().isoformat(),
                }).eq("id", opp["id"]).execute()
                sent += 1
                log.warning(f"[auto_post] SENT {opp['channel']} | {opp['source_url'][:70]}")
            else:
                db.table("opportunities").update({
                    "status": OpportunityStatus.approved,
                    "acted_at": __import__("datetime").datetime.utcnow().isoformat(),
                }).eq("id", opp["id"]).execute()
        except Exception as e:
            log.warning(f"[auto_post] FAILED {opp.get('source_url','')[:60]}: {e}")
    log.warning(f"[auto_post] Done — {sent} posted for user {user_id[:8]}")


async def _auto_scan_loop():
    await asyncio.sleep(60)
    while True:
        try:
            import logging
            log = logging.getLogger("cast.scan")
            from app.core.supabase import get_supabase
            from app.services.opportunity_service import OpportunityService
            from app.services.scanners.hn_scanner import scan_hn
            from app.services.scanners.reddit_scanner import scan_reddit
            from app.services.scanners.web_scanner import scan_web
            from app.services.scanners.youtube_scanner import scan_youtube
            from app.services.scanners.forum_scanner import scan_forums

            db = get_supabase()
            products_data = db.table("product_profiles").select("*").execute().data or []
            log.warning(f"[scan] Starting scan for {len(products_data)} product(s)")

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
                ingested = 0
                for raw in raw_lists:
                    if isinstance(raw, Exception):
                        continue
                    for opp_create in raw:
                        try:
                            await opp_service.ingest(opp_create)
                            ingested += 1
                        except Exception:
                            pass
                log.warning(f"[scan] Ingested {ingested} opps for product '{p_row.get('name')}'")

                # Auto-approve and post high-scoring pending opps
                await _auto_post_pending(p_row["user_id"])

        except Exception as e:
            import logging
            logging.getLogger("cast.scan").warning(f"[scan] Loop error: {e}")
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


@app.get("/admin/users")
def list_users(secret: str = ""):
    if secret != os.environ.get("CRON_SECRET", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    from app.core.database import get_db
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT user_id, COUNT(*) as cnt FROM opportunities GROUP BY user_id").fetchall()
    conn.close()
    return [{"user_id": r[0], "count": r[1]} for r in rows]


@app.post("/admin/reset-password")
def reset_password(user_id: str, new_password: str, secret: str = ""):
    if secret != os.environ.get("CRON_SECRET", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    from app.core.database import get_db
    import hashlib, hmac, secrets as sec
    salt = sec.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", new_password.encode(), salt.encode(), 260000)
    pw_hash = f"{salt}${dk.hex()}"
    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", [pw_hash, user_id])
    conn.commit()
    conn.close()
    return {"reset": True}


@app.post("/admin/seed-datum")
def seed_datum(secret: str = ""):
    if secret != os.environ.get("CRON_SECRET", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    from app.core.database import get_db
    import json as _json
    conn = get_db()
    existing = conn.execute("SELECT id FROM product_profiles WHERE name='DATUM+' LIMIT 1").fetchone()
    if existing:
        conn.close()
        return {"status": "already_exists", "id": existing[0]}
    import uuid as _uuid
    product_id = str(_uuid.uuid4())
    user_id = "61b06034-a360-4136-918a-4212c07e4a4b"
    keywords = _json.dumps([
        "construction management software", "procore alternative", "buildertrend alternative",
        "job costing", "construction payroll", "contractor software", "construction scheduling",
        "bid management", "change orders", "construction ai", "equipment diagnostics",
        "daily logs", "excavation software", "small contractor", "construction saas",
    ])
    conn.execute("""INSERT INTO product_profiles
        (id, user_id, name, tagline, description, target_audience, pain_point_solved, url, pricing_summary, keywords)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", [
        product_id, user_id, "DATUM+",
        "All-in-one construction management at $49/month — Procore alternative",
        "DATUM+ is an all-in-one construction management platform built for contractors who run real work. Job costing, payroll with live tax calculations, Gantt scheduling, AI field assistant (DATUM Ai™), equipment fault diagnostics (MECH-IQ™), Bidders IQ™ for contract discovery, GPS daily logs, change orders, RFIs, submittals, photo docs. Starting at $49/month — Procore starts at $10,000/year. 7-day free trial, no credit card required.",
        "Contractors, subcontractors, small construction companies, excavation crews, GCs running 3-20 jobs/year, construction business owners",
        "Procore costs $10,000/year. Buildertrend is residential-only. Nothing exists for the contractor running 3-20 jobs/year who needs real tools at a real price.",
        "https://lowlevellogic.org",
        "$49/mo Solo, $85/mo Starter, $199/mo Pro, $399/mo Enterprise. 7-day free trial.",
        keywords,
    ])
    conn.commit()
    conn.close()
    return {"status": "seeded", "id": product_id}


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
