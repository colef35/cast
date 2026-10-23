#!/usr/bin/env python3
"""Smoke check for the Phase 0 profile refactor (SPEC §4.1/§4.2).

Proves, without any network or real Supabase:
  1. The DATUM+ profile loads through the NEW path (config fallback →
     profile_loader) with all of its intelligence intact.
  2. A profile round-trips through ProductService + the local SQLite store
     with every §4.1 field preserved.
  3. The scorer drafts from profile data: with the DATUM+ profile loaded the
     draft is byte-for-byte the old hardcoded behaviour.
  4. A bare-bones second product (no DATUM+ data anywhere) scores and drafts
     from generic fallbacks — the engine is product-agnostic.
  5. Every scanner module imports cleanly (no stale datum_profile imports).

Run:  python3 scripts/smoke_profiles.py
"""
import asyncio
import os
import sys
import tempfile
from uuid import uuid4

# Isolate from any real environment BEFORE importing app modules.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "cast-smoke.db")
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_SERVICE_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["CAST_DEFAULT_PROFILE"] = "datum+"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

failures = []


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)
    if not cond:
        failures.append(label)


async def main():
    from app.models.opportunity import Channel, OpportunityCreate
    from app.models.product_profile import ProductProfileCreate
    from app.services.datum_profile import DATUM_PLUS_SEED
    from app.services.profile_intel import detect_feature, get_communities
    from app.services.profile_loader import load_active_profile, load_profile_from_config
    from app.services.product_service import ProductService
    from app.services.scorer import score_and_draft

    # 1 ── Config fallback loads DATUM+ through the new path ────────────────
    profile = load_profile_from_config()
    check("config fallback returns a profile", profile is not None)
    check("profile is DATUM+", profile.name == "DATUM+")
    check("reddit communities match seed", get_communities(profile, "reddit") == DATUM_PLUS_SEED["communities"]["reddit"])
    check("HN queries match seed", profile.search_queries.get("hackernews") == DATUM_PLUS_SEED["search_queries"]["hackernews"])
    check("feature map matches seed", len(profile.feature_map) == len(DATUM_PLUS_SEED["feature_map"]))
    check("buying signals match seed", profile.buying_signals == DATUM_PLUS_SEED["buying_signals"])

    # 2 ── DB round-trip through ProductService preserves §4.1 fields ───────
    user_id = uuid4()
    service = ProductService()
    created = await service.create(user_id, ProductProfileCreate(**DATUM_PLUS_SEED))
    loaded = await service.get(created.id, user_id)
    check("DB round-trip returns the profile", loaded is not None)
    check("round-trip keeps reddit communities", loaded.communities.get("reddit") == DATUM_PLUS_SEED["communities"]["reddit"])
    check("round-trip keeps feature map", len(loaded.feature_map) == 12)
    check("round-trip keeps voice templates", "DATUM+" in loaded.voice.draft_templates.get("reddit", ""))
    check("round-trip keeps competitors", loaded.competitors == ["Procore", "Buildertrend"])

    active = await load_active_profile(user_id)
    check("load_active_profile resolves from DB", active is not None and active.id == created.id)

    # 3 ── Scorer behaviour with DATUM+ loaded == the old hardcoded output ──
    opp = OpportunityCreate(
        product_id=loaded.id,
        user_id=user_id,
        channel=Channel.reddit,
        source_url="https://reddit.com/r/construction/example",
        source_title="Procore is too expensive — what do you use for job costing?",
        source_body=(
            "We are a small excavation crew running 8 jobs a year and Procore is "
            "killing us on price. Payroll is a headache and I am tracking costs in "
            "a spreadsheet. Looking for recommendations for something affordable."
        ),
    )
    relevance, roi, draft = score_and_draft(loaded, opp)
    expected_draft = (
        "This is exactly why we built DATUM+. full construction management at "
        "$49/month — fully covered, starting at $49/month (Procore alternative). "
        "7-day free trial, no card needed. https://lowlevellogic.org"
    )
    check("relevance > 0", relevance > 0)
    check("draft == legacy hardcoded DATUM+ draft", draft == expected_draft)
    check(
        "detect_feature maps procore/cost → $49/month feature",
        detect_feature(loaded, opp.source_title) == "full construction management at $49/month",
    )

    # 4 ── A second, unrelated product works with zero DATUM+ data ──────────
    other = await service.create(
        user_id,
        ProductProfileCreate(
            name="Acme Candles",
            tagline="Hand-poured candles that actually last",
            description="Small-batch scented candles.",
            target_audience="Candle buyers",
            pain_point_solved="Candles that burn out in a week",
            url="https://example.com/candles",
            keywords=["scented candles"],
        ),
    )
    opp2 = OpportunityCreate(
        product_id=other.id,
        user_id=user_id,
        channel=Channel.reddit,
        source_url="https://reddit.com/r/candles/example",
        source_title="Looking for scented candles that last more than a week?",
        source_body="Every candle I buy burns out fast and loses its scent. Does anyone know a brand that actually lasts? Recommendations welcome please.",
    )
    _, _, draft2 = score_and_draft(other, opp2)
    check("generic profile drafts with its own name", "Acme Candles" in draft2)
    check("generic profile draft has no DATUM+ bleed", "DATUM" not in draft2 and "Procore" not in draft2)
    check("generic profile has no reddit communities", get_communities(other, "reddit") == [])
    check("generic feature falls back to tagline", detect_feature(other, "anything") == other.tagline)

    # 5 ── All scanner modules import cleanly ───────────────────────────────
    import importlib

    for mod in (
        "app.services.scanners.reddit_scanner",
        "app.services.scanners.hn_scanner",
        "app.services.scanners.web_scanner",
        "app.services.scanners.youtube_scanner",
        "app.services.scanners.forum_scanner",
        "app.services.scanners.quora_scanner",
    ):
        importlib.import_module(mod)
    check("all six scanners import", True)


asyncio.run(main())

if failures:
    print(f"\nSMOKE FAILED: {len(failures)} check(s)")
    sys.exit(1)
print("\nSMOKE OK — all checks passed")
