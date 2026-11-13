#!/usr/bin/env python3
"""fixcoords.py: find places whose coordinates lie outside their own state and correct them from Wikipedia (#767).
Usage: fixcoords.py [--audit]   (--audit only lists, changes nothing)
Audit: for US places with a `states` list (FIPS codes, as in the `states` of data/geo/geo.json), a place whose point is more than TOL degrees from every one of its states is flagged
(TOL lets coast and island places pass).
Fix: for a flagged place the coordinates of its Wikipedia article (the imgwiki title first, then the titles in its `sources`) are read with the en.wikipedia.org API
(prop=coordinates, primary); they are taken only when they fall inside, or within TOL of, one of the place's own states. Otherwise the place is left and listed as
'unresolved'. A changed place keeps its other fields; `lat` and `lon` are the only edits. Prints 'fixed: id old -> new' and 'unresolved: id ...' lines for the pull request.
WRONG_PICTURES: titles whose Wikipedia article matched a different place of the same name (found by reading the matches); their picture is removed and the title
returns to photos/places/missing.json so the photo passes can try again with the corrected coordinates."""
import sys, os, json, glob, math, re, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TOL = 0.1
WRONG_PICTURES = {'Raymond': 'a Spanish museum painting for Raymond, Rhode Island', 'Trout Pond': 'a West Virginia pond for Trout Pond, Maine'}

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
        if d.get('country') != '840' or not st or any(s not in geo for s in st) or 'lat' not in d: continue
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

def fix(data_dir, geo, get):
    fixed, unresolved = [], []
    for f, d in audit(data_dir, geo):
        new = None
        for t in titles(d):
            c = wiki_coords(t, get)
            if c and near_states(c[0], c[1], d['states'], geo): new = c; break
        if not new: unresolved.append(d['id']); continue
        raw = open(f).read(); old = (d['lat'], d['lon']); d['lat'], d['lon'] = round(new[0], 4), round(new[1], 4)
        open(f, 'w').write(json.dumps(d, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
        fixed.append((d['id'], old, (d['lat'], d['lon'])))
    return fixed, unresolved

def drop_pictures(root):
    pp, mp = os.path.join(root, 'photos/places/places.json'), os.path.join(root, 'photos/places/missing.json')
    P = json.load(open(pp)); M = json.load(open(mp)); gone = []
    import datetime
    t0 = datetime.datetime.now(datetime.timezone.utc)
    now, soon = t0.isoformat(), (t0 + datetime.timedelta(seconds=1)).isoformat()   # a valid entry (attempts >= 1, expiresAt after checkedAt) that is already due, so the photo passes retry it at once
    for t in WRONG_PICTURES:
        if t in P:
            f = P.pop(t).get('f')
            if f and os.path.exists(os.path.join(root, 'photos/places', f)): os.remove(os.path.join(root, 'photos/places', f))
            M[t] = {'status': 'nophoto', 'checkedAt': now, 'expiresAt': soon, 'attempts': 1}; gone.append(t)
    if gone:
        open(pp, 'w').write(json.dumps(P, ensure_ascii=False, indent=0)); open(mp, 'w').write(json.dumps(M, ensure_ascii=False, indent=0))
    return gone

if __name__ == '__main__':
    sys.path.insert(0, HERE); import wm
    geo = {s['id']: s['g'] for s in json.load(open(os.path.join(ROOT, 'data/geo/geo.json')))['states']}
    if '--audit' in sys.argv:
        for f, d in audit(os.path.join(ROOT, 'data/places'), geo): print('flagged:', d['id'], d['name'], d['place'], d['lat'], d['lon'])
        sys.exit(0)
    fixed, unresolved = fix(os.path.join(ROOT, 'data/places'), geo, wm.get)
    for i, o, n in fixed: print('fixed: %s %s -> %s' % (i, o, n))
    for i in unresolved: print('unresolved:', i)
    for t in drop_pictures(ROOT): print('picture removed: %s (%s)' % (t, WRONG_PICTURES[t]))
    print('%d fixed, %d unresolved' % (len(fixed), len(unresolved)))
