"""firstview.py: the first-view weight budget (#369). The first draw is bound by the bytes the phone line must carry (the page, the map library, the world places and the journeys file) and by which hosts it must reach, so those are blocked on here. Timings are not: they jitter too much (see perf-ab).
Raise a limit on purpose, in this file, in the pull request that needs it."""
import gzip, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Brotli bytes (quality 5) of what a phone fetches before the first draw: the page, the map library, the world places and (since #377) the journeys file. 12 Nov 2026 (#678, owner: the main address is Cloudflare Pages, which serves Brotli; the header check showed GitHub Pages serves gzip only): the budget counts Brotli, measured 380,251 bytes, limit 381,000 (the gzip limit was 407,000 on a total of about 405,500, so the margin is about the same as the 0.2% the owner agreed). Gzip is still printed for information, with no limit. A client that gets only gzip is not protected by this number.
FIRST_VIEW_BR_MAX = 381_000
# Outside hosts the first view may reach (map tiles, glyphs, satellite, elevation). A new one fails the check; add it here only on purpose.
HOSTS_ALLOWED = {'tiles.openfreemap.org', 'server.arcgisonline.com', 's3.amazonaws.com'}

def first_view_files(root=ROOT):
    lib = sorted(f for f in os.listdir(root) if re.fullmatch(r'maplibre-gl-[\d.]+\.js', f))
    return ['index.html'] + lib + ['api/places/main/index-world.json', 'api/places/main/cards-world.json', 'api/journeys/main.json']

def gzip_size(path):
    with open(path, 'rb') as f:
        return len(gzip.compress(f.read(), 9, mtime=0))

def brotli_size(path):
    """Brotli quality 5 (Python's brotli module when installed, else Node's zlib: the same library, the same bytes)."""
    try:
        import brotli
        with open(path, 'rb') as f:
            return len(brotli.compress(f.read(), quality=5))
    except ImportError:
        js = "const z=require('zlib'),b=require('fs').readFileSync(process.argv[1]);process.stdout.write(String(z.brotliCompressSync(b,{params:{[z.constants.BROTLI_PARAM_QUALITY]:5,[z.constants.BROTLI_PARAM_SIZE_HINT]:b.length}}).length))"
        return int(subprocess.check_output(['node', '-e', js, path]))

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
    total = gz_total = 0
    for f in first_view_files(root):
        p = os.path.join(root, f)
        n = brotli_size(p); g = gzip_size(p); total += n; gz_total += g
        out.append('  first view: %-40s %9d br %9d gz' % (f, n, g))
    ok = total <= FIRST_VIEW_BR_MAX; bad += not ok
    out.append('%-52s %9d / %9d %s' % ('first view, brotli total', total, FIRST_VIEW_BR_MAX, 'ok' if ok else 'OVER'))
    out.append('%-52s %9d (no limit)' % ('first view, gzip total', gz_total))
    with open(os.path.join(root, 'index.html'), encoding='utf8') as f:
        hosts = resource_hosts(f.read())
    new = sorted(hosts - HOSTS_ALLOWED)
    bad += bool(new)
    out.append('%-52s %s' % ('first view, outside hosts', 'ok (%s)' % ', '.join(sorted(hosts)) if not new else 'NEW HOST: ' + ', '.join(new)))
    return out, bad
