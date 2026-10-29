#!/usr/bin/env python3
"""bounds_more.py [id ...]: park outlines for places that bounds.py (PAD-US, US only) did not give one, from two open sources:
  1. Wikidata/Wikimedia Commons: the park's Wikipedia article -> Wikidata item -> its map boundary file (property P3896, CC0).
  2. OpenStreetMap, through Nominatim: a boundary whose Wikidata id is the park's, or else one with a matching name that lies within 30 km of the park's point.
Writes data/outlines/<id>.json = {"n": name, "r": [flat ring, ...], "s": "wikidata" | "osm"} (same shape as bounds.py; "s" is the source) and
pipeline/reports/outlines_missing.md listing the places that still have none. Resumable: places with a file are skipped.
OpenStreetMap data is (c) OpenStreetMap contributors, ODbL: the app's credits say so."""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, os.path.join(ROOT, 'build')); import species
OUT = os.path.join(ROOT, 'data', 'outlines'); UA = 'ConnectedEarth/1.0 (https://github.com/sachinwankhede/connected-earth; data job)'
sys.setrecursionlimit(20000)
MAXPTS = 2500    # points per park, keeps a file well under the 400 KB budget
def path(i): return os.path.join(OUT, i + '.json')
def get(url, tries=4, pause=3):
    for t in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90).read().decode('utf-8')
        except Exception as ex: err = ex; time.sleep(pause * (t + 1))
    raise err
def toks(s): return {w for w in re.findall(r'[a-z]+', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()) if w not in ('national', 'state', 'park', 'the', 'of', 'and', 'reserve', 'nature') and len(w) > 2}
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))
def rdp(pts, tol):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]; dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy) or 1e-12
    d, k = max(((abs(dy * (x - x1) - dx * (y - y1)) / n), i) for i, (x, y) in enumerate(pts[1:-1], 1))
    if d <= tol: return [pts[0], pts[-1]]
    return rdp(pts[:k + 1], tol)[:-1] + rdp(pts[k:], tol)
def simplify_ring(r, tol):
    if tol == 0 or len(r) < 8: return r
    k = max(range(1, len(r) - 1), key=lambda i: (r[i][0] - r[0][0]) ** 2 + (r[i][1] - r[0][1]) ** 2)   # a closed ring has no chord: split at the point farthest from the start
    return rdp(r[:k + 1], tol)[:-1] + rdp(r[k:], tol)
def rings_of(geom):
    if geom['type'] == 'Polygon': polys = [geom['coordinates']]
    elif geom['type'] == 'MultiPolygon': polys = geom['coordinates']
    else: return []
    return [[(c[0], c[1]) for c in ring] for poly in polys for ring in poly[:1]]   # outer rings only
def pack(rings):
    tol = 0.0001
    while True:
        out = []
        for r in rings:
            s = simplify_ring(r, tol)
            if len(s) >= 4:
                flat = []
                for x, y in s: flat += [round(x, 4), round(y, 4)]
                out.append(flat)
        if sum(len(f) // 2 for f in out) <= MAXPTS or tol > 0.05: return out
        tol *= 1.6
def wikidata(e):
    t = None
    for s in e.get('sources', []):
        m = re.match(r'https://en\.wikipedia\.org/wiki/([^#?]+)', s.get('url', ''))
        if m and not s.get('title', '').startswith('Wikipedia: ' + 'List'): t = urllib.parse.unquote(m.group(1)); break
    if not t: return None, None
    j = json.loads(get('https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&format=json&props=claims&titles=' + urllib.parse.quote(t.replace('_', ' '))))
    for q, ent in j.get('entities', {}).items():
        if not q.startswith('Q'): continue
        v = ent.get('claims', {}).get('P3896')
        return q, (v[0]['mainsnak']['datavalue']['value'] if v and 'datavalue' in v[0]['mainsnak'] else None)
    return None, None
def from_commons(f):
    j = json.loads(get('https://commons.wikimedia.org/w/index.php?action=raw&title=' + urllib.parse.quote(f)))
    d = j.get('data', j); rings = []
    for ft in d.get('features', [d]) if d.get('type') == 'FeatureCollection' else [d]:
        rings += rings_of(ft.get('geometry', ft))
    return rings
def from_osm(e, qid):
    q = e['name'] + ', ' + (e.get('country') or '')
    r = json.loads(get('https://nominatim.openstreetmap.org/search?format=jsonv2&polygon_geojson=1&polygon_threshold=0.0005&extratags=1&limit=6&q=' + urllib.parse.quote(q)))
    time.sleep(1.1)
    want = toks(e['name']); best = None
    for x in r:
        g = x.get('geojson') or {}
        if g.get('type') not in ('Polygon', 'MultiPolygon'): continue
        if qid and (x.get('extratags') or {}).get('wikidata') == qid: return rings_of(g)
        near = km(e['lat'], e['lon'], float(x['lat']), float(x['lon'])) < 30
        t = toks(x.get('name', '') or x.get('display_name', '').split(',')[0])
        if near and want and len(want & t) / len(want | t) >= 0.5 and x.get('category') in ('boundary', 'leisure', 'landuse', 'natural') and best is None: best = rings_of(g)
    return best
def places():
    for p in species.files():
        e = json.load(open(p))
        if e.get('park') and e.get('lat') is not None and e.get('name'): yield e
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); want = sys.argv[1:]; got = 0; missing = []
    for e in places():
        if (want and e['id'] not in want) or os.path.exists(path(e['id'])): continue
        rings = None; src = None
        try:
            qid, shape = wikidata(e)
            if shape:
                rings = from_commons(shape); src = 'wikidata'
            if not rings:
                rings = from_osm(e, qid); src = 'osm'
        except Exception as ex: print('ERR', e['id'], ex, flush=True)
        out = pack(rings) if rings else []
        if not out: missing.append(e); print('none', e['id'], e['name'], flush=True); continue
        json.dump({'n': e['name'], 'r': out, 's': src}, open(path(e['id']), 'w'), separators=(',', ':'), ensure_ascii=False); got += 1
        print('ok', src, e['id'], e['name'], len(out), flush=True); time.sleep(0.5)
    os.makedirs(os.path.join(here, 'reports'), exist_ok=True)
    with open(os.path.join(here, 'reports', 'outlines_missing.md'), 'w') as f:
        f.write('# Places without an outline (%d)\n\n| id | name | country |\n|---|---|---|\n' % len(missing))
        for e in missing: f.write('| %s | %s | %s |\n' % (e['id'], e['name'], e.get('country', '')))
    print(got, 'new outlines;', len(missing), 'still without')
