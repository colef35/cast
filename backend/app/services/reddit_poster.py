"""
Posts Reddit comments using session-based auth (username + password).
No OAuth app required.
"""
import os
import httpx

UA = "Mozilla/5.0 (compatible; cast-bot/0.1)"
_session_cookie: str | None = None
_modhash: str | None = None


async def _login(client: httpx.AsyncClient) -> tuple[str, str]:
    username = os.environ["REDDIT_USERNAME"]
    password = os.environ["REDDIT_PASSWORD"]

    resp = await client.post(
        "https://www.reddit.com/api/login.json",
        data={
            "user": username,
            "passwd": password,
            "api_type": "json",
        },
        headers={"User-Agent": UA},
    )
    resp.raise_for_status()
    body = resp.json()
    errors = body.get("json", {}).get("errors", [])
    if errors:
        raise RuntimeError(f"Reddit login failed: {errors}")

    modhash = body["json"]["data"]["modhash"]
    cookie = resp.cookies.get("reddit_session", "")
    return modhash, cookie


async def post_comment(thread_url: str, comment_text: str) -> str:
    """
    Posts a comment to a Reddit thread. Returns the URL of the posted comment.
    thread_url: full Reddit permalink, e.g. https://reddit.com/r/construction/comments/abc123/...
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        modhash, cookie = await _login(client)

        # Extract the post fullname (t3_id) from the thread JSON
        json_url = thread_url.rstrip("/") + ".json?limit=1"
        resp = await client.get(json_url, headers={"User-Agent": UA})
        resp.raise_for_status()
        data = resp.json()
        post_id = data[0]["data"]["children"][0]["data"]["name"]  # e.g. t3_abc123

        # Post the comment
        resp = await client.post(
            "https://www.reddit.com/api/comment",
            data={
                "api_type": "json",
                "thing_id": post_id,
                "text": comment_text,
                "uh": modhash,
            },
            headers={
                "User-Agent": UA,
                "Cookie": f"reddit_session={cookie}",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        errors = body.get("json", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Reddit post failed: {errors}")

        things = body.get("json", {}).get("data", {}).get("things", [])
        if things:
            permalink = things[0]["data"].get("permalink", "")
            return f"https://reddit.com{permalink}"
        return thread_url
