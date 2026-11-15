#!/usr/bin/env python3
"""fixcoords.py: find places whose coordinates lie outside their own state and correct them from Wikipedia (#767).
Usage: fixcoords.py [--audit]   (--audit only lists, changes nothing)
Audit: for US places with a `states` list (FIPS codes, as in the `states` of data/geo/geo.json), a place whose point is more than TOL degrees from every one of its states is flagged
(TOL lets coast and island places pass).
Second source (#767): a place Wikipedia cannot place is looked up by name in PAD-US (USGS, public domain; host already allowed) restricted to the place's own state, so a Harriman State Park in New York
cannot match the one in Idaho; the centre of the biggest piece of the best name match is taken, again only when it falls inside, or within TOL of, the place's own state, and the name must match
(`padus_coords`; the fixed line says which source gave the coordinates).
Fix: for a flagged place the coordinates of its Wikipedia article (the imgwiki title first, then the titles in its `sources`) are read with the en.wikipedia.org API
(prop=coordinates, primary); they are taken only when they fall inside, or within TOL of, one of the place's own states. Otherwise the place is left and listed as
'unresolved'. A changed place keeps its other fields; `lat` and `lon` are the only edits. Prints 'fixed: id old -> new' and 'unresolved: id ...' lines for the pull request.
(The two pictures that came from a wrong same-named article, Raymond and Trout Pond, were removed by the first runs; the picture removal is gone, #887. Pictures are written only through lib/place_photos.py.)"""
import sys, os, json, glob, math, re, time, unicodedata, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TOL = 0.1
# Water bodies and island parks: their point is not inside any state's land, and the audit must not call that an error (#767). Listed by id, not guessed from the name.
WATER = {'greatlakes', 'gulf', 'npdrytortugas'}

def rings(g):
    for p in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]):
        yield p[0]

def inside(x, y, r):
    c = False
    for i in range(len(r)):
        x1, y1 = r[i]; x2, y2 = r[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c

def edge_dist(x, y, r):
    m = 9e9
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i], r[i - 1]; dx, dy = x2 - x1, y2 - y1
        t = 0 if dx == dy == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        m = min(m, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return m

def near_states(lat, lon, states, geo):
    """True when the point is inside, or within TOL degrees of, one of the states."""
    for s in states:
        for r in rings(geo[s]):
            if inside(lon, lat, r) or edge_dist(lon, lat, r) <= TOL: return True
    return False

def audit(data_dir, geo):
    out = []
    for f in sorted(glob.glob(os.path.join(data_dir, '*.json'))):
        d = json.load(open(f)); st = d.get('states') or []
        if d.get('id') in WATER or d.get('country') != '840' or not st or any(s not in geo for s in st) or 'lat' not in d: continue
        if not near_states(d['lat'], d['lon'], st, geo): out.append((f, d))
    return out

def titles(d):
    t = [d['imgwiki']] if d.get('imgwiki') else []
    for s in d.get('sources') or []:
        m = re.search(r'wikipedia\.org/wiki/([^#?]+)', s.get('url', ''))
        if m: t.append(urllib.parse.unquote(m.group(1)).replace('_', ' '))
    seen = []; [seen.append(x) for x in t if x not in seen]; return seen

def wiki_coords(title, get):
    q = 'https://en.wikipedia.org/w/api.php?action=query&prop=coordinates&coprimary=primary&redirects=1&format=json&titles=' + urllib.parse.quote(title)
    for p in ((get(q) or {}).get('query') or {}).get('pages', {}).values():
        c = (p.get('coordinates') or [None])[0]
        if c: return c['lat'], c['lon']
    return None

PADUS = 'https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query'
ABBR = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
        'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
        'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'}
GENERIC = set('national state park forest refuge wildlife monument historic historical site memorial recreation area preserve seashore lakeshore river the of and wilderness natural conservation management'.split())
def name_tokens(s): return {w for w in re.findall(r'[a-z]+', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace("'s", 's')) if w not in GENERIC and len(w) > 2}

TYPES = {'state': 'state', 'national': 'national', 'historic': 'historic', 'historical': 'historic'}
def type_words(s): return {TYPES[w] for w in re.findall(r'[a-z]+', (s or '').lower()) if w in TYPES}
def padus_coords(d, geo, get, min_score=0.6):
    """(lat, lon, unit name) from PAD-US for place d, or None. The query is restricted to the place's own state (one state: a place with several states is not handled here); the best name match
    needs token overlap (Jaccard) of min_score or more on the distinctive words of the name, and its biggest piece's centre must be inside, or within TOL of, the state."""
    st = d.get('states') or []; state = (d.get('place') or '').split(',')[0].strip(); ab = ABBR.get(state)
    want = name_tokens(d.get('name', '')) | name_tokens(d.get('short', ''))
    if len(st) != 1 or not ab or not want: return None
    key = sorted(want, key=len, reverse=True)[0].replace("'", "''")
    q = urllib.parse.urlencode(dict(where="State_Nm='%s' AND UPPER(Unit_Nm) LIKE '%%%s%%'" % (ab, key.upper()), outFields='Unit_Nm,GIS_Acres', returnGeometry='true', outSR='4326', maxAllowableOffset='0.01', f='json', resultRecordCount=100))
    feats = ((get(PADUS + '?' + q) or {}).get('features')) or []
    units = {}
    for f in feats:
        n = (f.get('attributes') or {}).get('Unit_Nm') or ''
        if n and f.get('geometry'): units.setdefault(n, []).extend(f['geometry'].get('rings') or [])
    best = None; wt = type_words(d.get('name', '')) | type_words(d.get('short', ''))
    for n, rs in units.items():
        if type_words(n) != wt: continue   # "Riverside Park" is not "Riverside State Park" (#767): state, national and historic must agree
        if not wt and re.sub(r'[^a-z]', '', n.lower()) not in {re.sub(r'[^a-z]', '', x.lower()) for x in (d.get('name'), d.get('short')) if x}: continue   # a bare name ("Riverside", "Raymond", "Sunset Lake") needs the unit of exactly that name: "Riverside Park" is another place (#767, #863)
        t = name_tokens(n); sc = len(want & t) / max(1, len(want | t)) if t else 0
        if sc >= min_score and rs and (best is None or sc > best[0]): best = (sc, n, rs)
    if not best: return None
    ring = max(best[2], key=lambda r: (max(x for x, y in r) - min(x for x, y in r)) * (max(y for x, y in r) - min(y for x, y in r)))
    lon = (max(x for x, y in ring) + min(x for x, y in ring)) / 2; lat = (max(y for x, y in ring) + min(y for x, y in ring)) / 2
    return (lat, lon, best[1]) if near_states(lat, lon, st, geo) else None

NOMINATIM = 'https://nominatim.openstreetmap.org/search'
def nominatim_coords(d, geo, get, min_score=0.6):
    """(lat, lon, name) from OpenStreetMap Nominatim, searched by the place's name and its state (one state only), or None. The result's own name must agree with the place's
    (Jaccard on the distinctive words, state / national / historic words equal) and the point must be inside, or within TOL of, the state: the same two guards as PAD-US."""
    st = d.get('states') or []; state = (d.get('place') or '').split(',')[0].strip()
    names = [n for n in (d.get('name'), d.get('short')) if n]
    if len(st) != 1 or not state or not names: return None
    want = name_tokens(names[0]) | name_tokens(d.get('short', '')); wt = type_words(names[0]) | type_words(d.get('short', ''))
    if not want: return None
    q = urllib.parse.urlencode(dict(q='%s, %s' % (names[0], state), countrycodes='us', format='jsonv2', limit=5))
    best = None
    for r in (get(NOMINATIM + '?' + q) or []):
        n = r.get('name') or (r.get('display_name') or '').split(',')[0]
        if type_words(n) != wt: continue
        t = name_tokens(n); sc = len(want & t) / max(1, len(want | t)) if t else 0
        try: lat, lon = float(r['lat']), float(r['lon'])
        except (KeyError, TypeError, ValueError): continue
        if sc >= min_score and near_states(lat, lon, st, geo) and (best is None or sc > best[0]): best = (sc, lat, lon, n)
    return (best[1], best[2], best[3]) if best else None

def fix(data_dir, geo, get, padus=None, osm=None):
    """padus: a function (place, geo) -> (lat, lon, unit) or None, tried after Wikipedia (main passes padus_coords with the real getter); None = Wikipedia only."""
    fixed, unresolved = [], []
    for f, d in audit(data_dir, geo):
        new = None; src = 'Wikipedia'
        for t in titles(d):
            c = wiki_coords(t, get)
            if c and near_states(c[0], c[1], d['states'], geo): new = c; break
        if not new and padus:
            c = padus(d, geo)
            if c: new = c[:2]; src = 'PAD-US "%s"' % c[2]
        if not new and osm:
            c = osm(d, geo)
            if c: new = c[:2]; src = 'OpenStreetMap "%s"' % c[2]
        if not new: unresolved.append(d['id']); continue
        raw = open(f).read(); old = (d['lat'], d['lon']); d['lat'], d['lon'] = round(new[0], 4), round(new[1], 4)
        open(f, 'w').write(json.dumps(d, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
        fixed.append((d['id'], old, (d['lat'], d['lon']), src))
    return fixed, unresolved

if __name__ == '__main__':
    sys.path.insert(0, HERE); import wm
    geo = {s['id']: s['g'] for s in json.load(open(os.path.join(ROOT, 'data/geo/geo.json')))['states']}
    if '--audit' in sys.argv:
        for f, d in audit(os.path.join(ROOT, 'data/places'), geo): print('flagged:', d['id'], d['name'], d['place'], d['lat'], d['lon'])
        sys.exit(0)
    def slow_get(u): time.sleep(1.1); return wm.get(u)   # Nominatim allows one request a second
    fixed, unresolved = fix(os.path.join(ROOT, 'data/places'), geo, wm.get, lambda d, g: padus_coords(d, g, wm.get), lambda d, g: nominatim_coords(d, g, slow_get))
    for i, o, n, src in fixed: print('fixed: %s %s -> %s (%s)' % (i, o, n, src))
    for i in unresolved: print('unresolved:', i)
    print('%d fixed, %d unresolved' % (len(fixed), len(unresolved)))
