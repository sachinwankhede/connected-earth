#!/usr/bin/env python3
"""outline_check.py: places whose own point lies outside their own outline (#977, docs/DATA-AUDIT.md, step 6).

outside(root, km) -> [(distance in km, place id), ...] for every place with an outline and a point where the point is not inside the outline
and is more than `km` kilometres from its nearest edge, farthest first. A point inside any ring counts as inside (rings are not told apart from holes: a
park outline is drawn as its parts). Read only; the validator turns the list into an error or a warning (build/validate_data.py, OUTSIDE_IS_ERROR)."""
import glob, json, math, os

def kind(name):
    """'refuge', 'forest' or 'park' when a unit's name says so, else None. The outline jobs drop these words when they compare names, so a Forest and a Refuge of one name would look alike
    (#1004: an Arapaho National Forest outline stood for the Arapaho National Wildlife Refuge, a Sequoia National Forest one for the National Park)."""
    n = (name or '').lower()
    return 'refuge' if 'refuge' in n or 'nwr' in n else 'forest' if 'forest' in n else 'park' if 'park' in n else None

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

if __name__ == '__main__':
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for d, pid in outside(root, float(sys.argv[1]) if sys.argv[1:] else 5.0): print('%7.1f km  %s' % (d, pid))
