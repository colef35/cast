"""
Shared Reddit session — logs in with ColeFar89 credentials once, reuses cookie for all reads + writes.
"""
import os
import httpx
from app.core.proxy import proxy_kwargs

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
_modhash: str | None = None
_cookies: dict = {}


async def get_session() -> tuple[str, dict]:
    """Returns (modhash, cookies). Logs in if needed."""
    global _modhash, _cookies
    if _modhash:
        return _modhash, _cookies

    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("REDDIT_USERNAME / REDDIT_PASSWORD not set")

    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
        # Get initial cookies
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
        resp.raise_for_status()
        body = resp.json()
        errors = body.get("json", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Reddit login failed: {errors}")

        _modhash = body["json"]["data"]["modhash"]
        _cookies = dict(resp.cookies)
        # merge initial cookies
        for k, v in client.cookies.items():
            _cookies[k] = v

    return _modhash, _cookies


async def reddit_get(url: str, params: dict = None) -> httpx.Response:
    modhash, cookies = await get_session()
    async with httpx.AsyncClient(follow_redirects=True, timeout=15, **proxy_kwargs()) as client:
        return await client.get(
            url,
            params=params,
            headers={"User-Agent": UA, "Authorization": f""},
            cookies=cookies,
        )


async def reddit_post(url: str, data: dict) -> httpx.Response:
    modhash, cookies = await get_session()
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
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
