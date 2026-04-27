"""
Posts replies to ContractorTalk (XenForo 2) threads.
Requires CT_USERNAME and CT_PASSWORD env vars.
"""
import os
import httpx
from bs4 import BeautifulSoup
from app.core.proxy import proxy_kwargs

BASE = "https://www.contractortalk.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

_token: str | None = None
_cookies: dict = {}


async def _get_session() -> tuple[str, dict]:
    global _token, _cookies
    if _token:
        return _token, _cookies

    username = os.environ.get("CT_USERNAME", "")
    password = os.environ.get("CT_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("CT_USERNAME / CT_PASSWORD not set")

    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
        resp = await client.get(f"{BASE}/login/", headers={"User-Agent": UA})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        token_el = soup.find("input", {"name": "_xfToken"})
        if not token_el:
            raise RuntimeError("Could not find _xfToken on login page")
        xf_token = token_el["value"]

        resp = await client.post(
            f"{BASE}/login/login",
            data={"login": username, "password": password, "_xfToken": xf_token, "remember": "1"},
            headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        if "login" in str(resp.url):
            raise RuntimeError("ContractorTalk login failed — check CT_USERNAME/CT_PASSWORD")

        _cookies = dict(client.cookies)
        # Re-fetch a token post-login for reply submissions
        resp2 = await client.get(BASE, headers={"User-Agent": UA})
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        token_el2 = soup2.find("input", {"name": "_xfToken"})
        _token = token_el2["value"] if token_el2 else xf_token
        _cookies = dict(client.cookies)

    return _token, _cookies


async def post_reply(thread_url: str, comment_text: str) -> str:
    """
    Posts a reply to a ContractorTalk thread.
    Returns the thread URL on success.
    """
    xf_token, cookies = await _get_session()

    async with httpx.AsyncClient(follow_redirects=True, timeout=20, **proxy_kwargs()) as client:
        client.cookies.update(cookies)

        # Fetch thread to get reply action URL and fresh token
        resp = await client.get(thread_url, headers={"User-Agent": UA})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        reply_form = soup.find("form", {"class": lambda c: c and "js-quickReply" in c}) or \
                     soup.find("form", action=lambda a: a and "reply" in str(a))
        if not reply_form:
            return None  # Thread closed or login failed

        action = reply_form.get("action", "")
        if not action.startswith("http"):
            action = BASE + action

        token_input = reply_form.find("input", {"name": "_xfToken"})
        fresh_token = token_input["value"] if token_input else xf_token

        resp = await client.post(
            action,
            data={"message": comment_text, "_xfToken": fresh_token, "_xfResponseType": "json"},
            headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded",
                     "X-Requested-With": "XMLHttpRequest"},
        )
        resp.raise_for_status()

    return thread_url
