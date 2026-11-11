"""lib/fetch.py: runtime guard ensuring all external downloads and network requests
route only to approved hosts defined in lib/allowed_sources.json.
Refuses unlisted hosts at run time."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_SOURCES_PATH = os.path.join(ROOT, "lib", "allowed_sources.json")

_allowed_hosts = None


def get_allowed_hosts():
    global _allowed_hosts
    if _allowed_hosts is None:
        if os.path.isfile(ALLOWED_SOURCES_PATH):
            with open(ALLOWED_SOURCES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            hosts = set(data.get("hosts", []))
            for src_info in data.get("sources", {}).values():
                for h in src_info.get("hosts", []):
                    hosts.add(h)
            _allowed_hosts = hosts
        else:
            _allowed_hosts = set()
    return _allowed_hosts


def check_url(url_or_request):
    """Verifies that the URL or Request points to an allowed host in lib/allowed_sources.json.
    Raises PermissionError if the host is unlisted or scheme is not http/https."""
    if isinstance(url_or_request, urllib.request.Request):
        url = url_or_request.full_url
    else:
        url = str(url_or_request)

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise PermissionError(f"URL scheme '{parsed.scheme}' not allowed: {url}")

    host = parsed.hostname
    if not host:
        raise PermissionError(f"URL missing valid hostname: {url}")

    allowed = get_allowed_hosts()
    if host not in allowed:
        raise PermissionError(
            f"Host '{host}' is not in lib/allowed_sources.json. "
            f"All downloads must use owner-approved sources: {url}"
        )
    return host


def urlopen(url_or_request, *args, **kwargs):
    """Guarded wrapper around urllib.request.urlopen that refuses unlisted hosts."""
    check_url(url_or_request)
    return urllib.request.urlopen(url_or_request, *args, **kwargs)


def fetch_bytes(url, headers=None, timeout=60):
    """Fetch raw bytes from an approved URL."""
    req = urllib.request.Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url, headers=None, timeout=60):
    """Fetch and parse JSON from an approved URL."""
    b = fetch_bytes(url, headers=headers, timeout=timeout)
    return json.loads(b.decode("utf-8"))


def fetch_text(url, headers=None, timeout=60, encoding="utf-8"):
    """Fetch decoded text from an approved URL."""
    b = fetch_bytes(url, headers=headers, timeout=timeout)
    return b.decode(encoding)
