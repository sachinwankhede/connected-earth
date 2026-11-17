#!/usr/bin/env python3
"""outline_check.py: places whose own point lies outside their own outline (#977, docs/DATA-AUDIT.md, step 6).

outside(root, km) -> [(distance in km, place id), ...] for every place with an outline and a point where the point is not inside the outline
and is more than `km` kilometres from its nearest edge, farthest first. A point inside any ring counts as inside (rings are not told apart from holes: a
park outline is drawn as its parts). Read only; the validator turns the list into an error or a warning (build/validate_data.py, OUTSIDE_IS_ERROR)."""
import glob, json, math, os, re, sys, unicodedata

def kind(name):
    """'refuge', 'forest' or 'park' when a unit's name says so, else None. The outline jobs drop these words when they compare names, so a Forest and a Refuge of one name would look alike
    (#1004: an Arapaho National Forest outline stood for the Arapaho National Wildlife Refuge, a Sequoia National Forest one for the National Park)."""
    n = (name or '').lower()
    return 'refuge' if 'refuge' in n or 'nwr' in n else 'forest' if 'forest' in n else 'park' if 'park' in n else None

STOP = set('national state park forest refuge wildlife nwr monument historic site memorial recreation area preserve seashore lakeshore river the of and wilderness natural conservation'.split())
def toks(s):
    """The words of a place or unit name that tell one from another (the words every park has are left out), as the outline jobs compare them."""
    return {w for w in re.findall(r'[a-z]+', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace("'s", 's')) if w not in STOP and len(w) > 2}

def inside(x, y, rings):
    ins = False
    for r in rings:
        pts = [(r[i], r[i + 1]) for i in range(0, len(r) - 1, 2)]
        j = len(pts) - 1
        for i in range(len(pts)):
            (xi, yi), (xj, yj) = pts[i], pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: ins = not ins
            j = i
    return ins

def _seg(px, py, ax, ay, bx, by):
    k = math.cos(math.radians(py)); ax, bx, px = ax * k, bx * k, px * k
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)) * 111.2

def distance_km(x, y, rings):
    return min((_seg(x, y, r[i], r[i + 1], r[i + 2], r[i + 3]) for r in rings for i in range(0, len(r) - 3, 2)), default=0.0)

def outside(root, km=5.0):
    out = []
    for f in sorted(glob.glob(os.path.join(root, 'data', 'outlines', '*.json'))):
        pid = os.path.basename(f)[:-5]; pf = os.path.join(root, 'data', 'places', pid + '.json')
        if not os.path.exists(pf): continue
        p = json.load(open(pf)); x = p.get('lng', p.get('lon')); y = p.get('lat')
        rings = [r for r in (json.load(open(f)).get('r') or []) if isinstance(r, list) and len(r) >= 4 and len(r) % 2 == 0]
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not rings or inside(x, y, rings): continue
        d = distance_km(x, y, rings)
        if d > km: out.append((round(d, 1), pid))
    return sorted(out, reverse=True)

SMALL_KM = 15   # an outline under this many km across is one small unit; the report notes it next to a name that does not fit

def span_km(rings):
    xs = [c for r in rings for c in r[0::2]]; ys = [c for r in rings for c in r[1::2]]
    return max((max(xs) - min(xs)) * 85.0, (max(ys) - min(ys)) * 111.2) if xs else 0.0

def review(root):
    """#977: outlines whose name does not fit the place, for a person to look at (read only; nothing is dropped). -> [(place id, place name, outline name, km across, [reasons])], most reasons first.
    Reasons: 'kind' (a forest for a refuge), 'extra words' (the outline's name has words the place's does not: a trail, a management area), 'missing words' (the place's name has words the outline's does not:
    the outline covers only part of what the place names), and 'small' when the outline is under SMALL_KM across."""
    out = []
    for f in sorted(glob.glob(os.path.join(root, 'data', 'outlines', '*.json'))):
        pid = os.path.basename(f)[:-5]; pf = os.path.join(root, 'data', 'places', pid + '.json')
        if not os.path.exists(pf): continue
        p = json.load(open(pf)); o = json.load(open(f)); a = toks(p.get('name')) | toks(p.get('short')); b = toks(o.get('n'))
        if not a or not b: continue
        why = []
        ka, kb = kind(p.get('name')), kind(o.get('n'))
        if ka and kb and ka != kb: why.append('kind')
        if b - a: why.append('extra words')
        if toks(p.get('name')) - b and (not toks(p.get('short')) or toks(p.get('short')) - b): why.append('missing words')
        km = span_km([r for r in (o.get('r') or []) if isinstance(r, list) and len(r) >= 4 and len(r) % 2 == 0])
        if why and km < SMALL_KM: why.append('small')
        if why: out.append((pid, p.get('name'), o.get('n'), round(km), why))
    return sorted(out, key=lambda t: (-len(t[4]), t[0]))

if __name__ == '__main__' and sys.argv[1:2] == ['review']:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rows = review(root)
    print('%d outlines to look at (%d with more than one reason)' % (len(rows), sum(1 for r in rows if len(r[4]) > 1)))
    for pid, pn, on, km, why in rows: print('%-26s %-40.40s | %-40.40s %4d km  %s' % (pid, pn, on, km, ', '.join(why)))
    sys.exit(0)

if __name__ == '__main__':
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for d, pid in outside(root, float(sys.argv[1]) if sys.argv[1:] else 5.0): print('%7.1f km  %s' % (d, pid))
