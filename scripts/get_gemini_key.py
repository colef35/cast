#!/usr/bin/env python3
"""
OAuth device flow → creates a Gemini API key automatically.
User only needs to visit one URL and click Allow.
"""
import json, time, sys
import urllib.request, urllib.parse

# gcloud public OAuth client (documented in google-cloud-sdk source)
CLIENT_ID     = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"
CLIENT_SECRET = "d-FL95Q19q7MQmFpd7hHD0Ty"
SCOPE         = "https://www.googleapis.com/auth/cloud-platform"

def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req  = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def gapi(method, url, token, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  API error {e.code}: {e.read().decode()}")
        return None

# ── 1. Start device flow ───────────────────────────────────────────────────────
print("Starting Google OAuth device flow...")
dev = post("https://oauth2.googleapis.com/device/code", {
    "client_id": CLIENT_ID, "scope": SCOPE,
})

print("\n" + "="*50)
print(f"  Open on your phone: {dev['verification_url']}")
print(f"  Enter code:         {dev['user_code']}")
print("="*50)
print("\nWaiting for you to approve...")

# ── 2. Poll for token ──────────────────────────────────────────────────────────
interval = dev.get("interval", 5)
token = None
while True:
    time.sleep(interval)
    try:
        r = post("https://oauth2.googleapis.com/token", {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "device_code": dev["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        if "access_token" in r:
            token = r["access_token"]
            print("✓ Authenticated")
            break
        if r.get("error") == "slow_down":
            interval += 5
    except Exception:
        pass

# ── 3. Pick a GCP project ──────────────────────────────────────────────────────
projects = gapi("GET", "https://cloudresourcemanager.googleapis.com/v1/projects", token)
items = [p for p in (projects or {}).get("projects", []) if p.get("lifecycleState") == "ACTIVE"]

if not items:
    print("No GCP projects found. Creating one...")
    op = gapi("POST", "https://cloudresourcemanager.googleapis.com/v1/projects", token, {
        "projectId": f"cast-{int(time.time())}",
        "name": "CAST",
    })
    project_id = op["projectId"] if op else None
else:
    project_id = items[0]["projectId"]
    print(f"✓ Using project: {project_id}")

if not project_id:
    print("Could not find or create a GCP project.")
    sys.exit(1)

# ── 4. Enable Generative Language API ─────────────────────────────────────────
print("Enabling Gemini API...")
gapi("POST",
    f"https://serviceusage.googleapis.com/v1/projects/{project_id}/services/generativelanguage.googleapis.com:enable",
    token, {})
time.sleep(3)  # let enablement propagate

# ── 5. Create API key ──────────────────────────────────────────────────────────
print("Creating API key...")
key_op = gapi("POST",
    f"https://apikeys.googleapis.com/v2/projects/{project_id}/locations/global/keys",
    token,
    {
        "displayName": "CAST Gemini Key",
        "restrictions": {
            "apiTargets": [{"service": "generativelanguage.googleapis.com"}]
        }
    }
)

if not key_op:
    print("Failed to create key. Try manually at aistudio.google.com/apikey")
    sys.exit(1)

# Operation may be async — poll for it
op_name = key_op.get("name", "")
if op_name.startswith("operations/"):
    for _ in range(10):
        time.sleep(2)
        result = gapi("GET", f"https://apikeys.googleapis.com/v2/{op_name}", token)
        if result and result.get("done"):
            key_op = result.get("response", key_op)
            break

key_string = key_op.get("keyString") or key_op.get("response", {}).get("keyString")

if not key_string:
    print("Key created but couldn't retrieve key string. Check GCP Console → API Keys.")
    sys.exit(1)

# ── 6. Write to .env ───────────────────────────────────────────────────────────
env_path = "/root/cast/backend/.env"
with open(env_path) as f:
    lines = f.readlines()

with open(env_path, "w") as f:
    for line in lines:
        if line.startswith("GEMINI_API_KEY=") or line.startswith("ANTHROPIC_API_KEY="):
            f.write(f"GEMINI_API_KEY={key_string}\n")
        else:
            f.write(line)

print(f"\n✓ GEMINI_API_KEY written to .env")
print(f"  Key: {key_string[:12]}...")
