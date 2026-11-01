#!/usr/bin/env python3
"""Compatibility helpers and validation for the approved photo manifests."""
import datetime
import hashlib
import json
import os
import re
import struct
import sys
import urllib.parse

PERMANENT = {"nophoto", "notcommons", "notphoto"}
ALLOWED_IMAGE_HOSTS = {"upload.wikimedia.org", "thumb.wikimedia.org"}
ALLOWED_LICENSE_HOSTS = {"creativecommons.org", "www.gnu.org", "artlibre.org"}


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def negative_entry(status, attempts=1, now=None):
    """Return a timestamped failure cache entry with capped retry delays."""
    now = now or _utcnow()
    attempts = max(1, int(attempts))
    if status in PERMANENT:
        delay = datetime.timedelta(days=180)
    else:
        delay = datetime.timedelta(hours=min(24 * 7, 2 ** min(attempts, 8)))
    return {
        "status": status,
        "checkedAt": now.isoformat(),
        "expiresAt": (now + delay).isoformat(),
        "attempts": attempts,
    }


def cache_active(value, now=None):
    """Legacy string entries have no expiry and are retried once during migration."""
    if not isinstance(value, dict) or not value.get("expiresAt"):
        return False
    try:
        expiry = datetime.datetime.fromisoformat(value["expiresAt"].replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=datetime.timezone.utc)
        return expiry > (now or _utcnow())
    except (TypeError, ValueError):
        return False


def failure_class(status, http_status=None):
    if status in PERMANENT or http_status in (404, 410):
        return "permanent"
    return "transient"


def image_info(path):
    """Read image MIME type and dimensions from the file signature, not its suffix."""
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return "image/png", struct.unpack(">II", data[16:24])
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        return "image/gif", struct.unpack("<HH", data[6:10])
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 4 <= len(data):
            if data[i] != 0xff:
                i += 1
                continue
            while i < len(data) and data[i] == 0xff:
                i += 1
            if i >= len(data):
                break
            marker = data[i]
            i += 1
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            if i + 2 > len(data):
                break
            size = struct.unpack(">H", data[i:i + 2])[0]
            if size < 2 or i + size > len(data):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", data[i + 3:i + 7])
                return "image/jpeg", (width, height)
            i += size
    return None


def safe_https(url, allowed_hosts=None):
    if not isinstance(url, str) or not url:
        return False
    try:
        parsed = urllib.parse.urlsplit(url)
        return (parsed.scheme == "https" and (allowed_hosts is None or parsed.hostname in allowed_hosts)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def safe_species_asset(value):
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("https://"):
        return safe_https(value, ALLOWED_IMAGE_HOSTS)
    decoded = urllib.parse.unquote(value)
    return not (re.match(r"^[a-z][a-z0-9+.-]*:", value, re.I) or value.startswith("/")
                or any(segment in (".", "..") for segment in decoded.split("/"))
                or "?" in value or "#" in value)


def migrate_places(manifest_path, photo_dir):
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    checked_at = _utcnow().isoformat()
    for title, row in manifest.items():
        license_url = row.get("lu", "")
        parsed = urllib.parse.urlsplit(license_url)
        if parsed.scheme == "http" and parsed.hostname in ALLOWED_LICENSE_HOSTS:
            row["lu"] = urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, parsed.fragment))
        relative = row.get("f", "")
        if not relative or os.path.isabs(relative) or any(part in (".", "..") for part in relative.split("/")):
            raise ValueError(f"{title}: invalid local mirror path")
        asset = os.path.join(photo_dir, relative)
        info = image_info(asset)
        if not info:
            raise ValueError(f"{title}: unsupported image data in {relative}")
        if info[1][0] <= 0 or info[1][1] <= 0:
            raise ValueError(f"{title}: invalid image dimensions in {relative}")
        row["mt"] = info[0]
        row["width"], row["height"] = info[1]
        with open(asset, "rb") as f:
            row["sha256"] = hashlib.sha256(f.read()).hexdigest()
        row.setdefault("checkedAt", checked_at)
        row.setdefault("fetchedAt", None)
        license_id = row.get("l", "").strip()
        license_url = row.get("lu", "")
        author = row.get("a", "").strip()
        is_public_domain = license_id.lower() in {"public domain", "cc0"}
        row["reviewStatus"] = "approved" if (
            author and author.lower() != "unknown author" and license_id
            and not license_id.lower().startswith("see ")
            and ((license_url and safe_https(license_url)) or is_public_domain)
            and safe_https(row.get("p"), {"commons.wikimedia.org"})
        ) else "legacy"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)


def validate():
    errors = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    place_dir = os.path.join(root, "photos", "places")
    with open(os.path.join(place_dir, "places.json"), encoding="utf-8") as f:
        places = json.load(f)
    for title, row in places.items():
        relative = row.get("f", "")
        if not isinstance(relative, str) or not relative or os.path.isabs(relative) or any(part in (".", "..") for part in relative.split("/")):
            errors.append(f"{title}: invalid local mirror path")
            continue
        image_path = os.path.join(place_dir, relative)
        if not os.path.isfile(image_path):
            errors.append(f"{title}: missing local image")
            continue
        info = image_info(image_path)
        if not info or info[1][0] <= 0 or info[1][1] <= 0 or row.get("mt") != info[0] or (row.get("width"), row.get("height")) != info[1]:
            errors.append(f"{title}: media type or dimensions do not match image data")
        with open(image_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if row.get("sha256") != digest:
            errors.append(f"{title}: local image hash does not match manifest")
        if not row.get("a") or not row.get("l"):
            errors.append(f"{title}: missing author or license identifier")
        if row.get("lu") and not safe_https(row["lu"]):
            errors.append(f"{title}: license URL must be HTTPS")
        if not safe_https(row.get("p"), {"commons.wikimedia.org"}):
            errors.append(f"{title}: invalid Commons source page")
        if row.get("reviewStatus") == "approved":
            if not row.get("a") or row["a"].lower() == "unknown author" or not row.get("l") or row["l"].lower().startswith("see "):
                errors.append(f"{title}: approved photo is missing explicit author or license metadata")
            if not (row.get("lu") and safe_https(row["lu"])) and row.get("l", "").lower() not in {"public domain", "cc0"}:
                errors.append(f"{title}: approved photo is missing a secure license URL")
    with open(os.path.join(root, "photos", "species.json"), encoding="utf-8") as f:
        species = json.load(f)
    for title, row in species.items():
        if not isinstance(row, list) or len(row) < 2 or not safe_species_asset(row[0]):
            errors.append(f"{title}: invalid or unsupported species image URL")
    if errors:
        raise ValueError("\n".join(errors))
    print(f"validated {len(places)} local place candidates and {len(species)} legacy species candidates")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_places(sys.argv[2], sys.argv[3])
    else:
        validate()
