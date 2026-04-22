#!/usr/bin/env python3
"""Run this once to apply the schema to your Supabase project."""
import os
import sys
from pathlib import Path
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars first.")
    sys.exit(1)

sql = Path(__file__).parent.parent / "supabase_schema.sql"
print(f"Applying schema from {sql} ...")

client = create_client(url, key)
client.postgrest.schema("public")

statements = [s.strip() for s in sql.read_text().split(";") if s.strip()]
for stmt in statements:
    try:
        client.rpc("exec_sql", {"sql": stmt}).execute()
        print(f"  OK: {stmt[:60]}...")
    except Exception as e:
        print(f"  SKIP (may already exist): {e}")

print("Done.")
