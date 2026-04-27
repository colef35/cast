import os
import urllib.parse
import urllib.request
import json
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])

CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
REDIRECT_URI = f"https://{RAILWAY_DOMAIN}/auth/youtube/callback"
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"


@router.get("/youtube")
def youtube_auth():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/youtube/callback")
def youtube_callback(code: str = None, error: str = None):
    if error or not code:
        return HTMLResponse(f"<h2>Error: {error or 'no code'}</h2>", status_code=400)

    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    try:
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=data, method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        tokens = json.loads(resp.read())
        refresh_token = tokens.get("refresh_token", "")

        if not refresh_token:
            return HTMLResponse("<h2>No refresh token returned. Try visiting /auth/youtube again.</h2>")

        # Update env var in memory so current process uses it immediately
        os.environ["YOUTUBE_REFRESH_TOKEN"] = refresh_token
        # Clear cached access token so next post refreshes with new token
        import app.services.youtube_poster as yt
        yt._access_token = None

        return HTMLResponse(f"""
        <h2>✅ YouTube Authorized!</h2>
        <p>New refresh token (save this to Railway env vars to persist after redeploy):</p>
        <pre style="background:#f0f0f0;padding:12px;word-break:break-all">{refresh_token}</pre>
        <p><strong>CAST is now posting to YouTube immediately.</strong></p>
        """)
    except Exception as e:
        return HTMLResponse(f"<h2>Token exchange failed: {e}</h2>", status_code=500)
