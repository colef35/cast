"""
Posts HackerNews comments as DatumPlus using session cookie auth.
"""
import os
import re
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _cookie() -> str:
    return os.environ.get("HN_COOKIE", "")


def _item_id(thread_url: str) -> str:
    """Extract HN item ID from URL."""
    m = re.search(r"id=(\d+)", thread_url)
    if m:
        return m.group(1)
    m = re.search(r"/item/(\d+)", thread_url)
    return m.group(1) if m else ""


async def post_comment(thread_url: str, comment_text: str) -> str:
    """
    Posts a comment to a HackerNews thread.
    Returns the URL of the reply thread.
    """
    item_id = _item_id(thread_url)
    if not item_id:
        raise ValueError(f"Could not extract item ID from {thread_url}")

    cookie = _cookie()
    if not cookie:
        raise RuntimeError("HN_COOKIE not set")

    headers = {
        "User-Agent": UA,
        "Cookie": f"user={cookie}",
        "Referer": thread_url,
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        # Fetch the thread to get the hmac token for the top-level comment form
        resp = await client.get(f"https://news.ycombinator.com/item?id={item_id}", headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the reply form for the top-level item (parent = item_id)
        # HN uses <input name="hmac"> and <input name="parent"> in comment forms
        form = None
        for f in soup.find_all("form", action=True):
            parent_input = f.find("input", {"name": "parent"})
            if parent_input and parent_input.get("value") == item_id:
                form = f
                break

        if not form:
            # Fallback: find any form with a textarea (comment box)
            for f in soup.find_all("form"):
                if f.find("textarea"):
                    form = f
                    break

        if not form:
            # Thread is too old or comments are closed — not an error, just skip
            return None

        hmac_val = form.find("input", {"name": "hmac"})
        if not hmac_val:
            raise RuntimeError("Could not find hmac token")

        # Post the comment
        resp = await client.post(
            "https://news.ycombinator.com/comment",
            data={
                "parent": item_id,
                "goto": f"item?id={item_id}",
                "hmac": hmac_val["value"],
                "text": comment_text,
            },
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()

    return f"https://news.ycombinator.com/item?id={item_id}"
