"""firstview.py: the first-view weight budget (#369). The first draw is bound by the bytes the phone line must carry (the page, the map library, the world places and the journeys file) and by which hosts it must reach, so those are blocked on here. Timings are not: they jitter too much (see perf-ab).
Raise a limit on purpose, in this file, in the pull request that needs it."""
import gzip, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 12 Nov 2026 (#680, owner: go ahead): raised from 407,000 to 408,000 for the conservation word on the species sheet (about 100 bytes).
# Gzip bytes (level 9, GitHub Pages serves gzip only) of what a phone fetches before the first draw: the page, the map library, the world places and (since #377) the journeys file. 4 Nov 2026: 396,072 bytes after #398 removed the unused LAND literal (was 410,781); limit = about 2% above, rounded up to the next KB.
FIRST_VIEW_GZIP_MAX = 408_000
# Outside hosts the first view may reach (map tiles, glyphs, satellite, elevation). A new one fails the check; add it here only on purpose.
HOSTS_ALLOWED = {'tiles.openfreemap.org', 'server.arcgisonline.com', 's3.amazonaws.com'}

def first_view_files(root=ROOT):
    lib = sorted(f for f in os.listdir(root) if re.fullmatch(r'maplibre-gl-[\d.]+\.js', f))
    return ['index.html'] + lib + ['api/places/main/index-world.json', 'api/places/main/cards-world.json', 'api/journeys/main.json']

def gzip_size(path):
    with open(path, 'rb') as f:
        return len(gzip.compress(f.read(), 9, mtime=0))

def resource_hosts(html):
    """Hosts the page loads from: head/resource tags and the map's own addresses. Plain links (<a href>, Wikipedia pages for the reader) are not loads and are left out."""
    hosts = set()
    for m in re.finditer(r'<(?:link|script|img|image|iframe)\b[^>]*?\b(?:src|href)=["\']https?://([^/"\'\s]+)', html):
        hosts.add(m.group(1))
    for m in re.finditer(r'\b(?:GLYPHS|STYLES|DEM_TILES|SAT_TILES)\s*=\s*[^;]*', html):
        hosts.update(re.findall(r'https?://([^/"\'\s]+)', m.group(0)))
    for m in re.finditer(r'\btype:\s*["\'](?:vector|raster|raster-dem|geojson)["\'],\s*url:\s*["\']https?://([^/"\'\s]+)', html):
        hosts.add(m.group(1))
    return hosts

def check(root=ROOT):
    """Returns (lines to print, number of failures)."""
    out, bad = [], 0
    total = 0
    for f in first_view_files(root):
        n = gzip_size(os.path.join(root, f)); total += n
        out.append('  first view: %-40s %9d gz' % (f, n))
    ok = total <= FIRST_VIEW_GZIP_MAX; bad += not ok
    out.append('%-52s %9d / %9d %s' % ('first view, gzip total', total, FIRST_VIEW_GZIP_MAX, 'ok' if ok else 'OVER'))
    with open(os.path.join(root, 'index.html'), encoding='utf8') as f:
        hosts = resource_hosts(f.read())
    new = sorted(hosts - HOSTS_ALLOWED)
    bad += bool(new)
    out.append('%-52s %s' % ('first view, outside hosts', 'ok (%s)' % ', '.join(sorted(hosts)) if not new else 'NEW HOST: ' + ', '.join(new)))
    return out, bad
