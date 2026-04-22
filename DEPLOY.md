# CAST Deployment Guide

## 1. Supabase

1. Go to supabase.com → New project
2. SQL Editor → paste contents of `supabase_schema.sql` → Run
3. Settings → API → copy **Project URL** and **service_role** key

## 2. Reddit App

1. reddit.com/prefs/apps → Create App
2. Type: **script**
3. Copy client ID (under app name) and client secret

## 3. Backend — Railway (free tier works)

1. Install Railway CLI: `npm i -g @railway/cli`
2. `railway login`
3. From `cast/backend/`:
   ```
   railway init
   railway up
   ```
4. Set env vars in Railway dashboard (or CLI):
   ```
   railway variables set SUPABASE_URL=...
   railway variables set SUPABASE_SERVICE_KEY=...
   railway variables set ANTHROPIC_API_KEY=...
   railway variables set REDDIT_CLIENT_ID=...
   railway variables set REDDIT_CLIENT_SECRET=...
   railway variables set REDDIT_USER_AGENT=cast-bot/0.1 by u/YOUR_USERNAME
   ```
5. Copy your Railway deployment URL (e.g. `https://cast-api.up.railway.app`)

## 4. Local dev (optional)

```bash
cp backend/.env.example backend/.env
# fill in .env values
docker-compose up
```

API docs at http://localhost:8000/docs

## 5. Seed DATUM+ product

```bash
export CAST_API_URL=https://your-railway-url.up.railway.app
export CAST_USER_ID=your-supabase-user-uuid
python scripts/seed_product.py
```

## 6. Android app

1. Open `cast/android/` in Android Studio
2. In `di/NetworkModule.kt` replace `baseUrl` with your Railway URL
3. In `ui/screens/QueueViewModel.kt` replace `TODO_replace_with_real_user_id` with your UUID
4. Run on device

## 7. Trigger your first scan

```bash
curl -X POST 'https://your-railway-url.up.railway.app/scan/all/PRODUCT_ID?user_id=USER_ID'
```

Opportunities appear in the Android app queue within seconds.
