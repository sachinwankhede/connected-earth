#!/usr/bin/env python3
"""dupes.py: drop a park that is the same place as a bigger one listed under another unit name.
PAD-US sometimes lists one park twice ("Cherry Creek State Park" and "Cherry Creek Reservior"). Two parks count as the same place when their
centres are within 8 km and their distinctive words (leaving out park/state/lake-style filler) are the same or more than half shared. The bigger park (more acres) stays. --selftest checks the rules without the web."""
import math, re, sys
STOP = set('national state park forest recreation area historic site natural preserve conservation the of and lake reservoir reservior wildlife management'.split())
MAX_KM = 8

def toks(name): return {w for w in re.findall(r'[a-z]+', name.lower().replace("'s", 's')) if w not in STOP and len(w) > 2}
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))
def same(a, b):
    if km(a['lat'], a['lon'], b['lat'], b['lon']) > MAX_KM: return False
    x, y = toks(a['name']), toks(b['name'])
    if not x or not y: return False
    return len(x & y) / len(x | y) > 0.5

def dedupe(parks):
    """parks: dicts with name, lat, lon, acres. Returns (kept, dropped) with the bigger park of each pair kept."""
    kept, dropped = [], []
    for p in sorted(parks, key=lambda q: -(q.get('acres') or 0)):
        twin = next((k for k in kept if same(p, k)), None)
        if twin: dropped.append((p['name'], twin['name']))
        else: kept.append(p)
    order = {id(p): i for i, p in enumerate(parks)}
    return sorted(kept, key=lambda p: order[id(p)]), dropped

def selftest():
    P = lambda n, lat, lon, ac: dict(name=n, lat=lat, lon=lon, acres=ac)
    ok = []
    def t(label, got, want): ok.append(got == want); print(('ok  ' if got == want else 'FAIL'), label, '' if got == want else (got, want))
    k, d = dedupe([P('Cherry Creek State Park', 39.64, -104.84, 3300), P('Cherry Creek Reservior', 39.65, -104.85, 900)]); t('same park, other unit name', [p['name'] for p in k], ['Cherry Creek State Park'])
    k, d = dedupe([P('Cherry Creek Reservior', 39.65, -104.85, 5000), P('Cherry Creek State Park', 39.64, -104.84, 3300)]); t('the bigger one stays', [p['name'] for p in k], ['Cherry Creek Reservior'])
    k, d = dedupe([P('Honey Creek State Park', 40.8, -92.9, 800), P('Honey Creek Resort', 40.81, -92.91, 300)]); t('state park and its resort count as one', len(k), 1)
    k, d = dedupe([P('Rock Creek State Park', 41.8, -90.3, 500), P('Rock Creek State Park', 34.1, -91.2, 400)]); t('same name far apart stays', len(k), 2)
    k, d = dedupe([P('Lake Macbride State Park', 41.8, -91.6, 2000), P('Lake Darling State Park', 41.2, -91.7, 1000)]); t('different parks stay', len(k), 2)
    k, d = dedupe([P('Stone State Park', 42.5, -96.5, 1000), P('Stone Hills State Park', 42.52, -96.52, 400)]); t('near neighbours with different words stay', len(k), 2)
    if not all(ok): sys.exit(1)
if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest()
