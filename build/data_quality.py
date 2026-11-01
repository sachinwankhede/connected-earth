#!/usr/bin/env python3
"""Print an informational summary of data-quality indicators available offline."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.photo_registry import safe_https


def read_json(path):
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def photo_metadata(root):
    manifest = read_json(os.path.join(root, "photos", "places", "places.json"))
    complete = 0
    for row in manifest.values():
        digest = row.get("sha256")
        complete += bool(
            row.get("mt") in {"image/jpeg", "image/png", "image/gif"}
            and type(row.get("width")) is int and row["width"] > 0
            and type(row.get("height")) is int and row["height"] > 0
            and isinstance(digest, str) and re.fullmatch(r"[a-fA-F0-9]{64}", digest)
            and isinstance(row.get("a"), str) and row["a"].strip()
            and isinstance(row.get("l"), str) and row["l"].strip()
            and safe_https(row.get("p"), {"commons.wikimedia.org"})
        )
    return complete, len(manifest)


def place_ids(root):
    links = read_json(os.path.join(root, "data", "links.json"))
    return links, list(links["order"])


def outline_coverage(root, ids):
    outline_dir = os.path.join(root, "data", "outlines")
    available = sum(os.path.isfile(os.path.join(outline_dir, place_id + ".json")) for place_id in ids)
    return available, len(ids)


def cross_link_endpoints(root, links, ids):
    nodes_by_place = {}
    for place_id in ids:
        ecosystem = read_json(os.path.join(root, "data", place_id + ".json"))
        nodes_by_place[place_id] = {node["id"] for node in ecosystem["nodes"]}

    total = unresolved = 0
    for cross_link in links["cross"]:
        endpoints = cross_link.get("ends") or [
            endpoint for endpoint in (cross_link.get("from"), cross_link.get("to")) if endpoint
        ]
        for endpoint in endpoints:
            total += 1
            if endpoint.get("node") not in nodes_by_place.get(endpoint.get("eco"), ()):
                unresolved += 1
    return unresolved, total


def report(root=ROOT):
    complete, photo_total = photo_metadata(root)
    links, ids = place_ids(root)
    outlines, place_total = outline_coverage(root, ids)
    unresolved, endpoint_total = cross_link_endpoints(root, links, ids)
    species = read_json(os.path.join(root, "photos", "species.json"))

    return "\n".join((
        "## Informational data-quality summary",
        "",
        "Counts are informational; this report sets no quality thresholds and does not perform network lookups.",
        "",
        "| Indicator | Count | Definition and caveats |",
        "|---|---:|---|",
        f"| Place-photo metadata fields present | {complete}/{photo_total} | Candidate records in `photos/places/places.json` with supported MIME type, positive integer dimensions, 64-character SHA-256, non-empty author/license, and an HTTPS Commons source page. Existing photo validation separately checks these values against local image files. |",
        f"| Place outlines present | {outlines}/{place_total} | Place IDs in `data/links.json` `order` with a corresponding `data/outlines/<id>.json` file; absence does not necessarily mean an outline is expected. |",
        f"| Unresolved cross-place link endpoints | {unresolved}/{endpoint_total} | Endpoints in `data/links.json` `cross` whose place or node ID is not found in the main-app place files. This follows the endpoint integrity check used by the build. |",
        f"| Species-photo attribution metadata | unavailable ({len(species)} legacy candidates) | `photos/species.json` stores image paths and labels, not author/license records, so comparable completeness cannot be counted from this source. |",
        "",
    ))


if __name__ == "__main__":
    print(report())
