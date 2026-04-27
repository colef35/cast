import os, sqlite3, json
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", "/tmp/cast.db"))


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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

        CREATE TABLE IF NOT EXISTS product_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tagline TEXT NOT NULL,
            description TEXT NOT NULL,
            target_audience TEXT NOT NULL,
            pain_point_solved TEXT NOT NULL,
            url TEXT,
            pricing_summary TEXT,
            keywords TEXT DEFAULT '[]',
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
    conn.commit()
    conn.close()
