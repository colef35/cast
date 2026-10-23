# CAST — Universal Marketing Platform
### A Low Level Logic product · lowlevellogic.org
**Spec v1 — 2026-10-22**

---

## 1. The idea

CAST is a **listening-first marketing agent**. Every marketing tool on the market
starts with *posting* — scheduling content, blasting ads, automating outreach.
CAST starts with *listening*: it watches the public conversations where buyers
actually decide (Reddit first, then X, Hacker News, LinkedIn, YouTube comments,
niche forums), finds the moments where someone is asking for exactly what you
sell, and drafts the reply — in your voice, under your rules, with a human on
the approve button until you say otherwise.

The name is the metaphor: you don't chase customers, you **cast a net where the
fish already are.**

Nothing in the engine knows or cares what the product is. DATUM+ was the first
profile, not the product. A contractor, a SaaS founder, a plumber, and a
novelty candle shop all run the same loop with different profiles.

**Positioning line:** *CAST — marketing that listens first.*

**Brand decision (Cole, 2026-10-22): CAST IS THE FACE.** The apex domain
lowlevellogic.org is the CAST product site — CAST is the headline brand,
sold straight as a legitimate marketing platform. Low Level Logic Labs is
the maker (footer / about credit), never the headline.

## 2. Why this wins

| The field | Their problem | CAST's answer |
|---|---|---|
| Social schedulers (Buffer, Hootsuite) | Shout into the void; no idea who's buying | CAST only speaks when a buying signal fires |
| Listening tools (Brand24, Mention) | $100+/mo dashboards that show you conversations and leave the work to you | CAST drafts the response, not just the alert |
| AI spam posters | Get accounts banned, torch brand trust | Human-approved queue, per-community rule checks, disclosure controls |
| Agencies | $2k+/mo retainers for the same loop done by hand | Agency loop at software price |

The moat is not the LLM calls — anyone can draft a reply. The moat is
(1) **intent scoring** that separates "ready to buy" from "just chatting,"
(2) **community trust**: rule-aware, rate-limited, ban-resistant engagement,
and (3) **the learning loop**: every outcome (upvotes, replies, clicks,
conversions, removals) feeds the scorer.

## 3. The core loop

```
LISTEN → SCORE → DRAFT → APPROVE → ENGAGE → LEARN
```

1. **LISTEN** — Platform adapters stream posts/comments matching a product
   profile's keywords, subreddits/communities, competitors, and problem phrases.
2. **SCORE** — Each hit is classified by intent and ranked:
   - `ASKING_FOR_REC` — "what do you guys use for X?" *(highest value)*
   - `COMPETITOR_PAIN` — venting about a rival product
   - `HOW_TO` — a problem your product solves, asked in the open
   - `BUYING_SIGNAL` — pricing, comparisons, switching language
   - `COMPLAINT` — your own product mentioned negatively (defense/recovery)
   - `NOISE` — everything else, dropped
   Score = intent weight × community fit × recency × author quality.
3. **DRAFT** — Claude writes the reply in the profile's voice: helpful first,
   product second, no hard pitch unless the thread invites it. Generates 2–3
   variants (helpful / expert / casual).
4. **APPROVE** — The queue (already built in cast's Android app; web queue is
   the MVP addition). Swipe to approve, edit, or kill. Nothing posts without a
   human until the user unlocks autopilot rules for that community.
5. **ENGAGE** — Posts via the platform adapter, inside rate limits and the
   community's self-promo rules. Disclosure toggle per profile.
6. **LEARN** — Tracks the reply's life: score, comments, removals, mod actions,
   click/conversion callbacks. Outcomes retrain the scorer's weights per
   profile and per community.

## 4. Universalization — what changes in the codebase

The current repo is a single-product agent. These are the deltas, in order:

### 4.1 Product profiles replace the DATUM seed
`scripts/seed_product.py` becomes a **profile model** (Supabase table +
onboarding flow):
- Product: name, URL, one-liner, pricing page
- Pitch points + proof points (user-supplied, never invented)
- Keywords, problem phrases, competitor names
- Target communities (per platform) + blocked communities
- Voice profile: tone sliders + 3–5 example posts in the user's own words
- Guardrails: claims CAST may never make, topics to avoid

**Killer onboarding:** paste your product URL → CAST scrapes the site, builds
the draft profile, suggests keywords and communities. User edits, done.
No Supabase keys, no CLI, no Railway variables — that's the difference between
a repo and a product.

### 4.2 Multi-tenancy
Supabase auth already exists in the stack. Add workspaces: one user → many
product profiles → per-profile queues, scores, and history. Row-level security
on every table. This is the line between "Cole's tool" and "a platform."

### 4.3 Platform adapter interface
One interface, many ears:
```python
class PlatformAdapter:
    def search(self, profile, since) -> list[Signal]      # LISTEN
    def post_reply(self, signal, text) -> PostResult      # ENGAGE
    def track(self, post_id) -> Outcome                   # LEARN
    def community_rules(self, community) -> RuleSet       # guardrails
```
- **MVP:** Reddit (exists today — harden it)
- **Phase 2:** Hacker News, Bluesky, YouTube comments (cheap/free APIs)
- **Phase 3:** X and LinkedIn (paid APIs → paid tiers only)

### 4.4 Web queue
The Android queue proves the workflow; the **web queue at
app.lowlevellogic.org** is what makes it universal — nobody's business
customers install an APK. Android stays as the power-user client.

## 5. The Low Level Logic home — domain & hosting plan

**Current state (verified 2026-10-22):**
- lowlevellogic.org DNS is on Cloudflare ✓ (nameservers:
  melissa/owen.ns.cloudflare.com) — the domain is Cole's, at Cloudflare.
- The apex A record points at a **dead Railway fallback returning 404** —
  the site is currently *down*, served by the same Railway from the
  Oct 21 breach notice.
- `www` has **no DNS record at all**.
- A landing page already exists as a repo (The-V-Standard-Landing-page).

**Target state:**
| Host | Purpose | Served by |
|---|---|---|
| `lowlevellogic.org` | **CAST product site — CAST is the face** (maker credit: Low Level Logic Labs) | Cloudflare Pages (from GitHub) |
| `www.lowlevellogic.org` | Redirect to apex | Cloudflare |
| `cast.lowlevellogic.org` | Redirect to apex (CAST lives at the root) | Cloudflare |
| `app.lowlevellogic.org` | Web queue + dashboard | Cloudflare Pages + Workers |
| API backend | Existing Python backend, containerized | Off Railway (exit the breach surface); any container host, Cloudflare Tunnel in front |

Moving the public face onto Cloudflare closes three problems at once: the 404,
the missing www, and the Railway dependency for the brand domain.

## 6. Tiers (pricing sketch — Cole's call)

- **Listener — free / $19** — signals dashboard, no drafting. The hook.
- **Engager — $49/mo** — drafts + approval queue, 1 product, Reddit + 1 more
  platform. The core business tier.
- **Autopilot — $149/mo** — rules-bound auto-engagement, multi-product,
  X/LinkedIn adapters, conversion tracking. For agencies and serious sellers.

## 7. Compliance & trust (non-negotiable)

- Per-community rule engine: self-promo ratios, account-age/karma minimums,
  no-go subs — checked *before* a draft is ever queued.
- Rate limits per platform, per account, with jitter — no burst signatures.
- AI-disclosure toggle per profile; default honest.
- Ban-risk meter on every connected account; CAST slows itself down before a
  platform does it for you.
- No engagement on posts by minors' accounts, no medical/financial advice
  threads, no astroturfed reviews — hard exclusions, not settings.

## 8. MVP definition

Ships when a stranger can: go to cast.lowlevellogic.org → sign up → paste a
product URL → confirm the auto-built profile → connect Reddit → see scored
signals within the hour → approve a drafted reply from the web queue → watch
its outcome. DATUM+ runs as profile #1 — a customer, not the codebase.

**Cut from MVP:** X/LinkedIn adapters, auto-posting, Android parity, teams.

## 9. Roadmap

- **Phase 0 — Foundations:** domain fix (Pages + www + cast subdomain),
  profiles refactor (§4.1), multi-tenancy (§4.2). *The repo stops being
  DATUM-shaped here.*
- **Phase 1 — MVP:** web queue, onboarding-by-URL, Reddit adapter hardened,
  Stripe billing. First paying strangers.
- **Phase 2 — Reach:** HN/Bluesky/YouTube adapters, learning-loop v1
  (outcome-weighted scoring).
- **Phase 3 — Autopilot:** rules-bound auto-engage, X/LinkedIn, agency
  workspaces.

## 10. Open decisions for Cole

1. Launch wedge: truly universal on day one, or construction/trades first
   (home turf, DATUM+ as proof) with the universal engine underneath?
   *Spec recommends: universal engine, trades-first marketing.*
2. ~~CAST stays the product name under Low Level Logic Labs?~~ **RESOLVED
   (Cole, 2026-10-22): CAST is the face — it headlines lowlevellogic.org;
   Low Level Logic Labs is the maker credit.**
3. Android app: keep as companion, or freeze it and go web-first?
4. Pricing tiers above — gut check.

---
*Prepared by Blaze for Cole Farrar / Low Level Logic Labs. Source repo:
github.com/colef35/cast (backend, Android client, Supabase schema,
DEPLOY.md — secrets scrubbed 2026-10-22, commit a5a1ab8).*
