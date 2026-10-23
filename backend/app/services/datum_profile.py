"""
Profile #1 seed data — DATUM+.

DATUM+ is CAST's first *customer*, not part of the codebase (SPEC §4.1).
Everything DATUM+-specific that used to be hardcoded across the scanners and
the scorer — keywords, subreddits, search queries, buying signals, draft
voices, the feature map — lives here as plain profile data, in exactly the
shape of a `ProductProfileCreate` payload. The engine reads it from the
`product_profiles` table like any other product; this module exists so the
seed scripts (and the /admin/seed-datum endpoint) have one canonical copy.

To onboard another product, write another seed dict like this one or create
the profile through the /products API — see PROFILES.md.
"""

DATUM_PLUS_SEED = {
    "name": "DATUM+",
    "tagline": "All-in-one construction management at $49/month — Procore alternative",
    "description": (
        "DATUM+ is an all-in-one construction management platform built for contractors "
        "who run real work. Job costing, payroll with live tax calculations, Gantt scheduling, "
        "AI field assistant (DATUM Ai™), equipment fault diagnostics (MECH-IQ™), Bidders IQ™ "
        "for contract discovery, GPS daily logs, change orders, RFIs, submittals, photo docs, "
        "and IDP™ document processing. Starting at $49/month — Procore starts at $10,000/year. "
        "7-day free trial, no credit card required."
    ),
    "target_audience": (
        "Contractors, subcontractors, small construction companies, excavation crews, "
        "GCs running 3–20 jobs/year, construction business owners"
    ),
    "pain_point_solved": (
        "Procore costs $10,000/year. Buildertrend is residential-only. "
        "Nothing exists for the contractor running 3–20 jobs/year who needs real tools at a real price."
    ),
    "url": "https://lowlevellogic.org",
    "pricing_summary": "$49/mo Solo, $85/mo Starter, $199/mo Pro, $399/mo Enterprise. 7-day free trial.",
    "keywords": [
        "construction management software", "procore alternative", "buildertrend alternative",
        "job costing", "construction payroll", "contractor software", "construction scheduling",
        "bid management", "change orders", "construction ai", "equipment diagnostics",
        "daily logs", "excavation software", "small contractor", "construction saas",
    ],
    "pitch_points": [
        "Job costing and budget tracking",
        "Payroll with live tax calculations",
        "Gantt scheduling and project timelines",
        "AI field assistant (DATUM Ai™)",
        "Equipment fault diagnostics (MECH-IQ™)",
        "Bid discovery and pipeline tracking (Bidders IQ™)",
        "GPS daily logs, change orders, RFIs, submittals, photo docs",
    ],
    "proof_points": [
        "Procore starts at $10,000/year; DATUM+ starts at $49/month",
        "7-day free trial, no credit card required",
    ],
    "problem_phrases": [
        "tired of procore", "procore too expensive", "alternative to procore",
        "alternative to buildertrend", "payroll headache", "manual process",
    ],
    "competitors": ["Procore", "Buildertrend"],
    "communities": {
        "reddit": [
            "construction", "civilengineering", "heavyequipment", "excavation",
            "ProjectManagement", "ConstructionManagers", "Homebuilding",
            "smallbusiness", "Entrepreneur", "SaaS", "contractor",
        ],
        "forum": [
            "https://www.contractortalk.com/forums/accounting-software-discussion.108/",
            "https://www.contractortalk.com/forums/business.16/",
            "https://www.contractortalk.com/forums/construction.4/",
            "https://www.contractortalk.com/forums/commercial-construction.84/",
            "https://www.contractortalk.com/forums/excavation.71/",
            "https://www.contractortalk.com/forums/general-discussion.2/",
        ],
    },
    "blocked_communities": [],
    "buying_signals": [
        "looking for", "recommend", "any suggestions", "what do you use",
        "tired of procore", "procore too expensive", "alternative to procore",
        "alternative to buildertrend", "frustrated with", "manual process", "spreadsheet",
        "job costing", "track costs", "payroll headache", "construction payroll",
        "scheduling software", "bid management", "change orders", "rfi",
        "pain point", "problem with", "wish there was", "does anyone know",
        "how do you handle", "what's your workflow", "tool for contractors",
        "app for contractors", "software for contractors", "calculate grade",
        "cut fill", "labor burden", "equipment hours", "field report",
        "daily log", "punch list", "subcontractor management",
    ],
    "domain_signals": [
        "construction", "excavat", "grading", "earthwork", "job cost",
        "procore", "buildertrend", "subcontract", "general contractor", "site work",
        "heavy equipment", "paving", "concrete", "framing", "field management",
        "punch list", "change order", "rfi", "submittal", "construction management",
        "construction software", "construction app", "construction scheduling",
        "construction payroll", "construction saas", "contractor software",
    ],
    "relevance_signals": {
        "forum": [
            "construction", "contractor", "excavat", "grading", "job cost", "procore",
            "buildertrend", "subcontract", "site work", "paving", "concrete", "estimat",
            "bid", "change order", "payroll", "scheduling", "field management",
            "software", "app", "tool", "manage", "track", "recommend",
        ],
        "quora": [
            "construction", "contractor", "procore", "buildertrend", "job cost",
            "payroll", "scheduling", "bid", "excavat", "subcontract",
        ],
    },
    "reject_signals": [
        "software contractor", "software engineer", "software developer",
        "programmer", "bootcamp", "tech recruiter", "immigration", "health insurance",
        "parallel construction", "intelligence agency", "law enforcement",
        "cryptocurrency", "blockchain",
    ],
    "search_queries": {
        "hackernews": [
            "construction management software", "procore alternative",
            "contractor software", "construction saas", "job costing",
            "construction productivity", "field management",
            "construction", "contractor", "general contractor", "subcontractor",
            "small business software field service", "operations software trades",
            "construction company", "building contractor", "excavation",
            "ask hn software construction", "construction workflow",
        ],
        "web": [
            "alternative to procore construction software",
            "construction management software too expensive",
            "best construction job costing software small contractor",
            "procore alternative affordable",
            "contractor software recommendation site:reddit.com OR site:contractortalk.com OR site:forum",
            "construction payroll software recommendation",
            "bid management software for contractors",
            "construction scheduling software small business",
            "what construction software do you use",
            "DATUM+ construction software review",
            "lowlevellogic.org construction",
        ],
        "youtube": [
            "construction management software review",
            "procore alternative 2024",
            "best construction software for small contractors",
            "construction job costing software",
            "contractor management app review",
            "construction scheduling software",
            "what software do contractors use",
            "procore too expensive alternative",
            "construction business software small contractor",
            "contractor job costing app review",
            "excavation contractor software",
            "construction payroll software review",
            "how to manage construction projects",
            "construction company software",
            "contractor business management tips",
            "construction field management app",
            "procore vs alternatives",
            "buildertrend alternative contractors",
            "running a construction business software",
            "contractor productivity tools",
        ],
        "quora": [
            "site:quora.com procore alternative construction",
            "site:quora.com best construction management software small contractor",
            "site:quora.com construction job costing software",
            "site:quora.com construction scheduling software recommendation",
            "site:quora.com contractor software recommendation",
            "site:quora.com buildertrend alternative",
            "site:quora.com construction payroll software",
            "site:quora.com construction app contractor",
        ],
    },
    "feature_map": [
        {"keywords": ["procore", "buildertrend", "expensive", "cost", "price", "afford"], "feature": "full construction management at $49/month"},
        {"keywords": ["job cost", "costing", "budget", "track cost", "over budget"], "feature": "job costing and budget tracking"},
        {"keywords": ["payroll", "wages", "labor cost", "labor burden", "employee cost"], "feature": "payroll with live tax calculations"},
        {"keywords": ["schedule", "scheduling", "gantt", "timeline", "deadline"], "feature": "Gantt scheduling and project timelines"},
        {"keywords": ["bid", "bidding", "contract", "proposal", "rfp", "sam.gov"], "feature": "bid discovery and pipeline tracking (Bidders IQ™)"},
        {"keywords": ["change order", "co ", "scope change", "extra work"], "feature": "change order management"},
        {"keywords": ["rfi", "submittal", "document", "paperwork"], "feature": "RFI, submittal, and document management"},
        {"keywords": ["equipment", "diagnostic", "fault", "maintenance", "hours"], "feature": "equipment diagnostics (MECH-IQ™)"},
        {"keywords": ["daily log", "field report", "gps", "site report"], "feature": "GPS daily logs and field reporting"},
        {"keywords": ["grade", "cut", "fill", "earthwork", "elevation", "slope"], "feature": "free grade and cut/fill calculator"},
        {"keywords": ["ai", "assistant", "automate", "intelligent"], "feature": "DATUM Ai™ field assistant"},
        {"keywords": ["photo", "documentation", "punch list"], "feature": "photo documentation and punch lists"},
    ],
    "default_feature": "all-in-one construction management",
    "free_tools": [
        "https://lowlevellogic.org/grade-calc",
        "https://lowlevellogic.org/labor-burden",
    ],
    "voice": {
        "tone": {},
        "example_posts": [],
        "draft_templates": {
            "hackernews": (
                "We built DATUM+ specifically for this — {feature} is one of the core workflows. "
                "It's a Procore alternative starting at $49/mo: {url}. "
                "Happy to share more if useful."
            ),
            "reddit": (
                "This is exactly why we built DATUM+. {feature} — fully covered, "
                "starting at $49/month (Procore alternative). 7-day free trial, no card needed. "
                "{url}"
            ),
            "linkedin": (
                "Relevant here — DATUM+ was built for exactly this problem. "
                "{feature}. All-in-one construction management at $49/month. "
                "7-day free trial: {url}"
            ),
            "twitter": "Built for this → DATUM+ covers {feature}. $49/mo, free trial: {url}",
        },
    },
    "guardrails": {
        "forbidden_claims": [],
        "avoid_topics": [],
        "disclose_ai": False,
    },
}


# Bundled seed profiles, keyed by slug — the config fallback in
# profile_loader resolves CAST_DEFAULT_PROFILE against this registry.
SEED_PROFILES = {
    "datum+": DATUM_PLUS_SEED,
    "datum": DATUM_PLUS_SEED,
}


def build_datum_seed_payload() -> dict:
    """The DATUM+ profile as a ProductProfileCreate-shaped dict (no id /
    user_id / timestamps — those are assigned at insert time)."""
    import copy

    return copy.deepcopy(DATUM_PLUS_SEED)
