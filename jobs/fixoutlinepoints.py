#!/usr/bin/env python3
"""fixoutlinepoints.py [--dry]: the places whose own point lies more than 5 km outside their own outline (#1004, docs/DATA-PLAN.md step 6). No network.

For each such place (lib/outline_check.py) it decides which of the two is wrong:
  - the outline is the place's own unit (named like it, the same kind of unit, and no more than FAR_KM away): the POINT was a rough sample, usually between the parts of a park
    drawn as several pieces. It moves onto the outline (the nearest point of its edge, nudged inward when that stays inside).
  - the outline is another unit (a National Forest for a National Wildlife Refuge, an Air National Guard station for a National Park, a pond in another state, a small piece of a
    large park): the OUTLINE is wrong. It is dropped with its credit record and the place goes on the missing list, so the outline job (data-outlines) looks again after its delay.
Prints one line per place, then the counts. --dry lists and changes nothing."""
import json, math, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outline_check as oc, outline_records
kind = oc.kind

STOP = set('national state park forest refuge wildlife nwr monument historic site memorial recreation area preserve seashore lakeshore river the of and wilderness natural conservation'.split())
def toks(s): return {w for w in re.findall(r'[a-z]+', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace("'s", 's')) if w not in STOP and len(w) > 2}

FAR_KM = 30   # a point this far outside its own outline: the outline is not the unit (the point is a rough sample, never that rough)

def same_unit(place, outline_name, km=0):
    """True when the outline is the place's own unit: named like it (its name or short name, as bounds.py compares them), of the same kind when both say a kind, and within FAR_KM."""
    want = toks(place.get('name')) | toks(place.get('short')); got = toks(outline_name)
    ka, kb = kind(place.get('name')), kind(outline_name)
    return bool(want and got and len(want & got) / len(want | got) >= 0.5) and not (ka and kb and ka != kb) and km <= FAR_KM

def nearest_edge_point(x, y, rings):
    """(lon, lat) of the point on the outline's edge nearest (x, y)."""
    best = None; k = math.cos(math.radians(y))
    for r in rings:
        for i in range(0, len(r) - 3, 2):
            ax, ay, bx, by = r[i], r[i + 1], r[i + 2], r[i + 3]
            dx, dy = (bx - ax) * k, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, (((x - ax) * k) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            px, py = ax + t * (bx - ax), ay + t * (by - ay); d = math.hypot((x - px) * k, y - py)
            if best is None or d < best[0]: best = (d, px, py)
    return best[1], best[2]

def snapped(x, y, rings):
    """A point on the outline near (x, y): the nearest edge point stepped a little toward the inside when that is inside, else the edge point itself."""
    ex, ey = nearest_edge_point(x, y, rings)
    for step in (0.003, 0.0015, 0.0007):   # about 300, 150 and 70 m
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            if oc.inside(ex + dx, ey + dy, rings): return round(ex + dx, 4), round(ey + dy, 4)
    return round(ex, 4), round(ey, 4)

def main(root=ROOT, dry=False, now=None):
    """-> (moved [(id, old, new, km)], dropped [(id, outline name, km)])."""
    rec = outline_records.OutlineRecords(root); moved, dropped = [], []
    for km, pid in oc.outside(root, 5.0):
        pf = os.path.join(root, 'data', 'places', pid + '.json'); of = os.path.join(root, 'data', 'outlines', pid + '.json')
        place = json.load(open(pf)); outline = json.load(open(of)); rings = [r for r in outline['r'] if len(r) >= 4 and len(r) % 2 == 0]
        if same_unit(place, outline.get('n'), km):
            x, y = snapped(place.get('lon'), place.get('lat'), rings)
            moved.append((pid, (place.get('lat'), place.get('lon')), (y, x), km))
            if not dry:
                text = open(pf, encoding='utf-8').read()
                text = re.sub(r'("lat":\s*)-?[\d.]+', lambda m: m.group(1) + repr(y), text, count=1); text = re.sub(r'("lon":\s*)-?[\d.]+', lambda m: m.group(1) + repr(x), text, count=1)
                open(pf, 'w', encoding='utf-8').write(text)
        else:
            dropped.append((pid, outline.get('n'), km))
            if not dry: rec.drop(pid, now=now)
    if dropped and not dry: rec.commit()
    return moved, dropped

if __name__ == '__main__':
    dry = '--dry' in sys.argv; moved, dropped = main(dry=dry)
    for pid, old, new, km in moved: print('%s point %s -> %s (was %s km outside)' % (pid, old, new, km))
    for pid, n, km in dropped: print('%s outline %r is another unit (point %s km outside): dropped' % (pid, n, km))
    print(len(moved), 'points', 'to move' if dry else 'moved', '|', len(dropped), 'outlines', 'to drop' if dry else 'dropped')
