#!/usr/bin/env python3
"""Seed DATUM+ as product profile #1 for CAST.

The seed content lives in ONE place — backend/app/services/datum_profile.py
(DATUM_PLUS_SEED) — because DATUM+ is a customer of the platform, not part of
the codebase (SPEC §4.1). This script just posts that payload to the API.
To seed a different product, point CAST_SEED_SLUG at another entry in
SEED_PROFILES or create the profile through the /products API (PROFILES.md).
"""
import copy, os, sys, requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.services.datum_profile import SEED_PROFILES

BASE = os.environ.get("CAST_API_URL", "http://localhost:8000")
USER_ID = os.environ.get("CAST_USER_ID")
SLUG = os.environ.get("CAST_SEED_SLUG", "datum+").strip().lower()

if not USER_ID:
    print("Set CAST_USER_ID env var (your Supabase user UUID).")
    sys.exit(1)

if SLUG not in SEED_PROFILES:
    print(f"Unknown CAST_SEED_SLUG '{SLUG}'. Known: {sorted(SEED_PROFILES)}")
    sys.exit(1)

payload = copy.deepcopy(SEED_PROFILES[SLUG])

resp = requests.post(f"{BASE}/products/", json=payload, params={"user_id": USER_ID})
resp.raise_for_status()
product = resp.json()
print(f"Created product: {product['id']}")
print(f"\nNow run a scan:")
print(f"  curl -X POST '{BASE}/scan/all/{product['id']}?user_id={USER_ID}'")
