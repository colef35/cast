"""Posts Reddit comments using the shared authenticated session."""
from app.services.reddit_session import reddit_get, reddit_post


async def post_comment(thread_url: str, comment_text: str) -> str:
    """
    Posts a top-level comment to a Reddit thread.
    Returns the URL of the posted comment.
    """
    # Fetch the post to get its fullname (t3_xxxxx)
    json_url = thread_url.rstrip("/") + ".json?limit=1"
    resp = await reddit_get(json_url)
    resp.raise_for_status()
    data = resp.json()
    post_fullname = data[0]["data"]["children"][0]["data"]["name"]  # e.g. t3_abc123

    resp = await reddit_post(
        "https://www.reddit.com/api/comment",
        {"thing_id": post_fullname, "text": comment_text},
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
