"""
Proxy configuration for outbound requests.
Set CAST_PROXY env var to a proxy URL, e.g.:
  http://user:pass@proxyhost:port
  socks5://user:pass@proxyhost:port

Supports rotating residential proxies (Brightdata, Smartproxy, etc.)
and Tor (socks5://127.0.0.1:9050).
"""
import os


def get_proxy() -> dict | None:
    url = os.environ.get("CAST_PROXY", "").strip()
    if not url:
        return None
    return {"http://": url, "https://": url}


def proxy_kwargs() -> dict:
    p = get_proxy()
    if p:
        return {"proxy": p}
    return {}
