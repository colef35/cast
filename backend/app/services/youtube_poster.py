"""
Posts YouTube comments using the YouTube Data API v3.
Requires YOUTUBE_REFRESH_TOKEN and YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET
env vars (OAuth 2.0 with youtube.force-ssl scope).
"""
import os
import re
import time
import httpx

TOKEN_URL = "https://oauth2.googleapis.com/token"
COMMENT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

_access_token: str | None = None
_token_expires_at: float = 0


def _video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else ""


async def _get_access_token() -> str:
    global _access_token, _token_expires_at
    if _access_token and time.time() < _token_expires_at - 60:
        return _access_token

    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError("YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN not all set")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        data = resp.json()
        _access_token = data["access_token"]
        _token_expires_at = time.time() + data.get("expires_in", 3600)

    return _access_token


async def post_comment(video_url: str, comment_text: str) -> str:
    """
    Posts a top-level comment on a YouTube video.
    Returns the video URL.
    """
    video_id = _video_id(video_url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from {video_url}")

    access_token = await _get_access_token()

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            COMMENT_URL,
            params={"part": "snippet"},
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": comment_text}
                    },
                }
            },
        )
        if resp.status_code == 403:
            # Comments disabled on this video
            return None
        resp.raise_for_status()

    return video_url
