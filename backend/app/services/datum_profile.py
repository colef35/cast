"""
Static DATUM+ intelligence — used to sharpen scoring and drafts.
"""

DATUM_PROFILE = {
    "name": "DATUM+",
    "tagline": "All-in-one construction management at $49/month — Procore alternative",
    "target_audience": (
        "Contractors, subcontractors, small construction companies, excavation crews, "
        "GCs running 3–20 jobs/year, construction business owners"
    ),
    "pain_point_solved": (
        "Construction software is either too expensive (Procore at $10k/year) or too limited. "
        "DATUM+ gives contractors real tools — job costing, payroll, scheduling, AI field assistant, "
        "equipment diagnostics, bid management, change orders, RFIs — starting at $49/month."
    ),
    "url": "https://lowlevellogic.org",
    "free_tools": [
        "https://lowlevellogic.org/grade-calc",
        "https://lowlevellogic.org/labor-burden",
    ],
    "keywords": [
        "construction management software", "procore alternative", "buildertrend alternative",
        "job costing software", "construction payroll", "contractor software",
        "construction scheduling", "bid management", "change order management",
        "construction ai", "equipment diagnostics", "daily logs", "rfi software",
        "construction app", "contractor app", "construction saas", "small contractor",
        "excavation software", "heavy civil", "construction productivity",
        "construction business", "field management", "grade calculator", "labor burden",
    ],
    "subreddits": [
        "construction", "civilengineering", "heavyequipment", "excavation",
        "ProjectManagement", "ConstructionManagers", "Homebuilding",
        "smallbusiness", "Entrepreneur", "SaaS", "contractor",
    ],
    "hn_queries": [
        "construction management software", "procore alternative",
        "contractor software", "construction saas", "job costing",
        "construction productivity", "field management",
    ],
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
}

# Draft voices per channel — helpful first, product second
DRAFT_VOICES = {
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
}

# Map pain keywords → relevant DATUM+ feature to highlight in draft
FEATURE_MAP = [
    (["procore", "buildertrend", "expensive", "cost", "price", "afford"], "full construction management at $49/month"),
    (["job cost", "costing", "budget", "track cost", "over budget"], "job costing and budget tracking"),
    (["payroll", "wages", "labor cost", "labor burden", "employee cost"], "payroll with live tax calculations"),
    (["schedule", "scheduling", "gantt", "timeline", "deadline"], "Gantt scheduling and project timelines"),
    (["bid", "bidding", "contract", "proposal", "rfp", "sam.gov"], "bid discovery and pipeline tracking (Bidders IQ™)"),
    (["change order", "co ", "scope change", "extra work"], "change order management"),
    (["rfi", "submittal", "document", "paperwork"], "RFI, submittal, and document management"),
    (["equipment", "diagnostic", "fault", "maintenance", "hours"], "equipment diagnostics (MECH-IQ™)"),
    (["daily log", "field report", "gps", "site report"], "GPS daily logs and field reporting"),
    (["grade", "cut", "fill", "earthwork", "elevation", "slope"], "free grade and cut/fill calculator"),
    (["ai", "assistant", "automate", "intelligent"], "DATUM Ai™ field assistant"),
    (["photo", "documentation", "punch list"], "photo documentation and punch lists"),
]


def detect_feature(text: str) -> str:
    text = text.lower()
    for keywords, feature in FEATURE_MAP:
        if any(k in text for k in keywords):
            return feature
    return "all-in-one construction management"
