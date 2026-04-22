#!/usr/bin/env bash
set -e
CAST_DIR="$(cd "$(dirname "$0")/.." && pwd)"

green() { echo -e "\033[32m$1\033[0m"; }
blue()  { echo -e "\033[34m$1\033[0m"; }
red()   { echo -e "\033[31m$1\033[0m"; }
ask()   { read -rp "$1: " "$2"; }

blue "=== CAST Bootstrap ==="
echo ""

# ── 1. Install Railway CLI (binary, no npm) ────────────────────────────────────
if ! command -v railway &>/dev/null; then
  blue "Installing Railway CLI..."
  mkdir -p "$HOME/.local/bin"
  curl -fsSL https://raw.githubusercontent.com/railwayapp/cli/master/install.sh \
    | RAILWAY_INSTALL_DIR="$HOME/.local/bin" bash
  export PATH="$HOME/.local/bin:$PATH"
fi
green "✓ Railway CLI: $(railway --version 2>/dev/null || echo 'installed')"

# ── 2. Python deps ─────────────────────────────────────────────────────────────
pip3 install -q requests httpx 2>/dev/null || true

# ── 3. Supabase — dashboard only, no CLI needed ────────────────────────────────
echo ""
blue "── Supabase ──"
echo "1. Go to https://supabase.com → create a new project"
echo "2. SQL Editor → paste the contents of cast/supabase_schema.sql → click Run"
echo "3. Settings → API → copy Project URL and service_role key"
echo ""
ask "Supabase Project URL (https://xxxx.supabase.co)" SUPABASE_URL
ask "service_role key" SUPABASE_SERVICE_KEY
green "✓ Supabase configured"

# ── 4. Anthropic ──────────────────────────────────────────────────────────────
echo ""
blue "── Anthropic ──"
echo "Get key at: https://console.anthropic.com/keys"
ask "Anthropic API key" ANTHROPIC_API_KEY

# ── 5. Reddit ─────────────────────────────────────────────────────────────────
echo ""
blue "── Reddit ──"
echo "1. reddit.com/prefs/apps → Create App"
echo "2. Type: script  |  Redirect URI: http://localhost"
echo "3. Client ID = short string under the app name"
ask "Reddit client ID" REDDIT_CLIENT_ID
ask "Reddit client secret" REDDIT_CLIENT_SECRET
ask "Your Reddit username" REDDIT_USERNAME

# ── 6. Write .env ──────────────────────────────────────────────────────────────
cat > "$CAST_DIR/backend/.env" <<EOF
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
REDDIT_CLIENT_ID=$REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET=$REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT=cast-bot/0.1 by u/$REDDIT_USERNAME
EOF
green "✓ .env written"

# ── 7. Deploy to Railway ───────────────────────────────────────────────────────
blue "Deploying to Railway (browser will open for login)..."
cd "$CAST_DIR/backend"
railway login --browserless 2>/dev/null || railway login

railway init --name cast-api 2>/dev/null || true

railway variables set \
  SUPABASE_URL="$SUPABASE_URL" \
  SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  REDDIT_CLIENT_ID="$REDDIT_CLIENT_ID" \
  REDDIT_CLIENT_SECRET="$REDDIT_CLIENT_SECRET" \
  "REDDIT_USER_AGENT=cast-bot/0.1 by u/$REDDIT_USERNAME"

railway up --detach
green "✓ Deploying... (takes ~2 min)"

railway domain generate 2>/dev/null || true
RAILWAY_URL=$(railway domain 2>/dev/null | head -1 || echo "CHECK_RAILWAY_DASHBOARD")
green "✓ Backend: https://$RAILWAY_URL"

# ── 8. User UUID ──────────────────────────────────────────────────────────────
echo ""
blue "── Your user ID ──"
echo "In Supabase: Authentication → Users → create a user → copy the UUID"
ask "Your Supabase user UUID" CAST_USER_ID

# ── 9. Seed DATUM+ ────────────────────────────────────────────────────────────
blue "Seeding DATUM+ product..."
cd "$CAST_DIR"
CAST_API_URL="https://$RAILWAY_URL" CAST_USER_ID="$CAST_USER_ID" python3 scripts/seed_product.py
PRODUCT_ID=$(CAST_API_URL="https://$RAILWAY_URL" CAST_USER_ID="$CAST_USER_ID" \
  python3 scripts/seed_product.py 2>/dev/null | grep "Created product:" | awk '{print $3}')

# ── 10. Summary ───────────────────────────────────────────────────────────────
echo ""
green "════════════════════════════════════"
green " CAST is live!"
green "════════════════════════════════════"
echo "API:      https://$RAILWAY_URL"
echo "API docs: https://$RAILWAY_URL/docs"
echo ""
echo "Trigger first scan:"
echo "  curl -X POST 'https://$RAILWAY_URL/scan/all/$PRODUCT_ID?user_id=$CAST_USER_ID'"
echo ""
blue "Android — two edits in Android Studio:"
echo "  NetworkModule.kt  → baseUrl = \"https://$RAILWAY_URL/\""
echo "  QueueViewModel.kt → userId  = \"$CAST_USER_ID\""
echo ""
green "Run the scan, open the app, start approving."
