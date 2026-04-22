#!/usr/bin/env bash
set -e
API="https://cast-production-e73f.up.railway.app"
USER_ID="00000000-0000-0000-0000-000000000001"

echo "Creating DATUM+ product profile..."
PRODUCT=$(curl -sf -X POST "$API/products/?user_id=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DATUM+ Field OS",
    "tagline": "Construction field intelligence in your pocket",
    "description": "DATUM+ is a mobile platform for construction crews — equipment diagnostics, grade and cut-fill calculations, underground utility detection, and AI-assisted field workflows. Built for the job site, not the office.",
    "target_audience": "Construction project managers, site supervisors, equipment operators, civil engineers",
    "pain_point_solved": "Field crews waste hours on manual grade calculations, equipment guesswork, utility locating calls, and running back to the office for data they should have on-site.",
    "url": "https://lowlevellogic.org/datum",
    "pricing_summary": "Free tier + Pro subscription",
    "keywords": ["construction technology","field management","equipment diagnostics","grade calculation","cut fill","utility detection","site management","construction app","construction productivity","heavy equipment","earthwork","grading","civil engineering","jobsite","superintendent"]
  }')

PRODUCT_ID=$(echo "$PRODUCT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Product ID: $PRODUCT_ID"

echo "Running scan on HN + Reddit..."
RESULTS=$(curl -sf -X POST "$API/scan/all/$PRODUCT_ID?user_id=$USER_ID")
COUNT=$(echo "$RESULTS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "Found $COUNT opportunities"

echo "Top 5 by ROI:"
echo "$RESULTS" | python3 -c "
import sys, json
opps = json.load(sys.stdin)
opps.sort(key=lambda x: x['roi_score'], reverse=True)
for o in opps[:5]:
    print(f\"  [{o['channel'].upper()}] {o['source_title'][:60]}\")
    print(f\"    ROI: {o['roi_score']} | Relevance: {o['relevance_score']}\")
    print(f\"    Draft: {o['draft'][:120]}...\")
    print()
"
