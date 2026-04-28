"""
Reddit session — OAuth2 password grant (preferred) with cookie fallback.
Requires REDDIT_USERNAME, REDDIT_PASSWORD env vars.
Optionally: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET for OAuth2 script app.
"""
import os
import httpx
from app.core.proxy import proxy_kwargs

UA = os.environ.get("REDDIT_USER_AGENT", "DATUM+CAST/0.1 by u/ColeFar89")

# OAuth2 state
_oauth_token: str | None = None
_oauth_expires: float = 0

# Cookie-based fallback state
_modhash: str | None = None
_cookies: dict = {}

_MODE: str = "none"


async def _try_oauth2() -> str | None:
    """Try Reddit OAuth2 password grant. Returns bearer token or None."""
    global _oauth_token, _oauth_expires, _MODE
    import time
    if _oauth_token and time.time() < _oauth_expires - 60:
        return _oauth_token

    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")

    if not (client_id and username and password):
        return None

    try:
        async with httpx.AsyncClient(timeout=20, **proxy_kwargs()) as client:
            resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "scope": "submit read",
                },
                auth=(client_id, client_secret or ""),
                headers={"User-Agent": UA},
            )
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token", "")
                expires_in = data.get("expires_in", 3600)
                if token:
                    _oauth_token = token
                    _oauth_expires = time.time() + expires_in
                    _MODE = "oauth2"
                    return token
    except Exception:
        pass
    return None


async def _try_cookie_login() -> tuple[str, dict]:
    """Try old-style cookie login. Returns (modhash, cookies)."""
    global _modhash, _cookies, _MODE
    if _modhash:
        return _modhash, _cookies

    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("REDDIT_USERNAME / REDDIT_PASSWORD not set")

    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
        await client.get("https://www.reddit.com/", headers={"User-Agent": UA})
        resp = await client.post(
            "https://www.reddit.com/api/login.json",
            data={"user": username, "passwd": password, "api_type": "json"},
            headers={
                "User-Agent": UA,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        if resp.status_code == 200:
            body = resp.json()
            errors = body.get("json", {}).get("errors", [])
            if not errors:
                _modhash = body["json"]["data"]["modhash"]
                _cookies = dict(resp.cookies)
                for k, v in client.cookies.items():
                    _cookies[k] = v
                _MODE = "cookie"
                return _modhash, _cookies

    raise RuntimeError(f"Reddit login failed (status {resp.status_code})")


async def reddit_get(url: str, params: dict = None) -> httpx.Response:
    token = await _try_oauth2()
    async with httpx.AsyncClient(follow_redirects=True, timeout=15, **proxy_kwargs()) as client:
        if token:
            return await client.get(
                url.replace("www.reddit.com", "oauth.reddit.com"),
                params=params,
                headers={"User-Agent": UA, "Authorization": f"Bearer {token}"},
            )
        modhash, cookies = await _try_cookie_login()
        return await client.get(url, params=params, headers={"User-Agent": UA}, cookies=cookies)


async def reddit_post(url: str, data: dict) -> httpx.Response:
    token = await _try_oauth2()
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
        if token:
            api_url = url.replace("www.reddit.com", "oauth.reddit.com")
            return await client.post(
                api_url,
                data={**data, "api_type": "json"},
                headers={"User-Agent": UA, "Authorization": f"Bearer {token}"},
            )
        modhash, cookies = await _try_cookie_login()
        return await client.post(
            url,
            data={**data, "uh": modhash, "api_type": "json"},
            headers={
                "User-Agent": UA,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
            cookies=cookies,
        )
