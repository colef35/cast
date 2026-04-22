#!/usr/bin/env python3
"""Seed DATUM+ as a product profile for CAST."""
import os, sys, requests

BASE = os.environ.get("CAST_API_URL", "http://localhost:8000")
USER_ID = os.environ.get("CAST_USER_ID")

if not USER_ID:
    print("Set CAST_USER_ID env var (your Supabase user UUID).")
    sys.exit(1)

payload = {
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
}

resp = requests.post(f"{BASE}/products/", json=payload, params={"user_id": USER_ID})
resp.raise_for_status()
product = resp.json()
print(f"Created product: {product['id']}")
print(f"\nNow run a scan:")
print(f"  curl -X POST '{BASE}/scan/all/{product['id']}?user_id={USER_ID}'")
