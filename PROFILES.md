# CAST Product Profiles

CAST is a universal marketing platform (see `SPEC.md`). The engine — scanners,
scorer, drafters — contains **no product-specific data**. Everything about a
product lives in its **product profile**: one row in the `product_profiles`
table. DATUM+ is profile #1, a customer of the platform, seeded from
`backend/app/services/datum_profile.py`.

## The profile model

Base fields (since the original schema):

| Field | Meaning |
|---|---|
| `name`, `tagline`, `description` | What the product is, in one line and in full |
| `target_audience`, `pain_point_solved` | Who it's for; the pain it removes |
| `url`, `pricing_url`, `pricing_summary` | Product site and pricing |
| `keywords` | Core vocabulary the scorer matches on |
| `user_id` / `workspace_id` | Owner, and the workspace it belongs to (SPEC §4.2) |

Phase 0 fields (SPEC §4.1 — migration `supabase_migration_002_product_profiles.sql`):

| Field | Shape | Used for |
|---|---|---|
| `pitch_points` | `list[str]` | Selling points the drafter may use — owner-supplied, never invented |
| `proof_points` | `list[str]` | Evidence (prices, trials, results) for drafts |
| `problem_phrases` | `list[str]` | How buyers describe the problem; scan/query fallback |
| `competitors` | `list[str]` | Rival names — competitor-pain signals, comparison queries |
| `communities` | `{platform: [..]}` | Target communities per platform, e.g. `{"reddit": ["SaaS"], "forum": ["https://…/section/"]}` |
| `blocked_communities` | `list[str]` | Never engage these, any platform |
| `buying_signals` | `list[str]` | Intent phrases scanners/scorer listen for |
| `domain_signals` | `list[str]` | The product world's topical vocabulary (relevance gate) |
| `relevance_signals` | `{channel: [..]}` | Per-channel relevance vocabulary overrides |
| `reject_signals` | `list[str]` | Phrases that mark a hit as noise |
| `search_queries` | `{channel: [..]}` | Per-channel queries: `hackernews`, `web`, `youtube`, `quora` |
| `feature_map` | `[{keywords, feature}]` | Pain keywords → the feature a draft highlights |
| `default_feature` | `str` | Feature used when no `feature_map` entry matches |
| `free_tools` | `list[str]` | Free tools / lead magnets drafts may point at |
| `voice` | `{tone, example_posts, draft_templates}` | Tone sliders (0–1), example posts in the owner's words, per-channel draft templates (`{name} {feature} {url} {tagline}` placeholders) |
| `guardrails` | `{forbidden_claims, avoid_topics, disclose_ai}` | Claims CAST may never make, topics to avoid, AI-disclosure preference |

**Fallback rule:** every field is optional. `app/services/profile_intel.py`
resolves each one: profile value if set, otherwise a generic default or a
value derived from the profile itself (e.g. search queries derived from
keywords + problem phrases + competitors). A profile with only a name,
tagline, description and keywords already scans, scores and drafts.

## Adding a product

**Via the API** (the normal path):

```bash
curl -X POST "http://localhost:8000/products/?user_id=<YOUR_USER_UUID>" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme Candles",
    "tagline": "Hand-poured candles that actually last",
    "description": "Small-batch scented candles.",
    "target_audience": "Candle buyers",
    "pain_point_solved": "Candles that burn out in a week",
    "url": "https://example.com/candles",
    "keywords": ["scented candles"],
    "communities": {"reddit": ["candles", "BuyItForLife"]}
  }'
```

**Via a seed** (bundled profiles): add a dict like `DATUM_PLUS_SEED` and
register it in `SEED_PROFILES` (see `backend/app/services/datum_profile.py`),
then `CAST_SEED_SLUG=<slug> CAST_USER_ID=<uuid> python3 scripts/seed_product.py`.

**Which profile runs:** scans are always per-profile (`POST /scan/all/{product_id}`).
For scripts and local runs, `app.services.profile_loader.load_active_profile()`
resolves the active profile: the user's most recently updated DB row first,
then the config fallback — `CAST_PROFILE_FILE=/path/profile.json`, or
`CAST_DEFAULT_PROFILE=datum+` for a bundled seed.

## Notes

- Profile #1's `keywords` are the production seed list (15 terms). The longer
  research list that used to sit in the old static profile lives on inside
  profile #1's `search_queries`, `domain_signals` and `buying_signals`.
- Local/SQLite mode stores list/dict fields as JSON text; Supabase stores
  `text[]` / `jsonb`. Same model either way.
- Verify the refactor anytime with `python3 scripts/smoke_profiles.py` —
  it proves the DATUM+ pipeline output is unchanged and that an unrelated
  product works with zero DATUM+ data.
