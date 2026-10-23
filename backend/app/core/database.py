import os, sqlite3, json
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", "/tmp/cast.db"))

# Profile columns added in Phase 0 (SPEC §4.1/§4.2). JSON-shaped values are
# stored as TEXT in SQLite and (de)serialised by app.core.supabase.
PROFILE_COLUMNS = {
    "workspace_id": "TEXT",
    "pricing_url": "TEXT",
    "pitch_points": "TEXT DEFAULT '[]'",
    "proof_points": "TEXT DEFAULT '[]'",
    "problem_phrases": "TEXT DEFAULT '[]'",
    "competitors": "TEXT DEFAULT '[]'",
    "communities": "TEXT DEFAULT '{}'",
    "blocked_communities": "TEXT DEFAULT '[]'",
    "buying_signals": "TEXT DEFAULT '[]'",
    "domain_signals": "TEXT DEFAULT '[]'",
    "relevance_signals": "TEXT DEFAULT '{}'",
    "reject_signals": "TEXT DEFAULT '[]'",
    "search_queries": "TEXT DEFAULT '{}'",
    "feature_map": "TEXT DEFAULT '[]'",
    "default_feature": "TEXT",
    "free_tools": "TEXT DEFAULT '[]'",
    "voice": "TEXT DEFAULT '{}'",
    "guardrails": "TEXT DEFAULT '{}'",
}


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_product_profiles(conn):
    """Add any missing Phase 0 columns to an existing product_profiles table."""
    existing = {r[1] for r in conn.execute("PRAGMA table_info(product_profiles)").fetchall()}
    for col, ddl in PROFILE_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE product_profiles ADD COLUMN {col} {ddl}")


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'trial',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS product_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            workspace_id TEXT,
            name TEXT NOT NULL,
            tagline TEXT NOT NULL,
            description TEXT NOT NULL,
            target_audience TEXT NOT NULL,
            pain_point_solved TEXT NOT NULL,
            url TEXT,
            pricing_summary TEXT,
            pricing_url TEXT,
            keywords TEXT DEFAULT '[]',
            pitch_points TEXT DEFAULT '[]',
            proof_points TEXT DEFAULT '[]',
            problem_phrases TEXT DEFAULT '[]',
            competitors TEXT DEFAULT '[]',
            communities TEXT DEFAULT '{}',
            blocked_communities TEXT DEFAULT '[]',
            buying_signals TEXT DEFAULT '[]',
            domain_signals TEXT DEFAULT '[]',
            relevance_signals TEXT DEFAULT '{}',
            reject_signals TEXT DEFAULT '[]',
            search_queries TEXT DEFAULT '{}',
            feature_map TEXT DEFAULT '[]',
            default_feature TEXT,
            free_tools TEXT DEFAULT '[]',
            voice TEXT DEFAULT '{}',
            guardrails TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'starter',
            active INTEGER NOT NULL DEFAULT 1,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_title TEXT NOT NULL,
            source_body TEXT NOT NULL,
            relevance_score REAL NOT NULL,
            roi_score REAL NOT NULL,
            draft TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            acted_at TEXT
        );
    """)
    _migrate_product_profiles(conn)
    conn.commit()
    conn.close()
