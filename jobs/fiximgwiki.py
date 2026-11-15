#!/usr/bin/env python3
"""fiximgwiki.py: give the places that share a Wikipedia title their own (#908; docs/DATA-PLAN.md).
Usage: fiximgwiki.py [--dry]   (run from the repository root; --dry lists and changes nothing). Host: en.wikipedia.org (already allowed), through jobs/wm.py.

Five titles are the `imgwiki` of ten places, so placepictures skips them (a picture keyed by title could land on the wrong place). Two of the ten carry a title that belongs to a different place
(`gulf`, the Northern Gulf of Mexico, has "Gulf Islands National Seashore"; `ozarks`, the Ozark habitat, has "Ozark National Scenic Riverways"), four are real parks that share a name across states
(Harriman, Village Creek), two keep the title they have (it is the right one), and `sdponca` looks like a duplicate of `neponca` (Ponca State Park lies wholly in Nebraska).
PROPOSED lists, for the six places that need one, the titles to try in order. A title is taken only when its article exists, is not a disambiguation page, has a primary coordinate within the place's
radius (30 km for a park, 600 km for a region), and no other place already uses it. Otherwise the place is left and listed `unresolved`. Only `imgwiki` is edited.
`sdponca` is never touched: the job lists it as `owner-decision` while it shares a title, because removing a place is the owner's call."""
import json, math, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)

# place id -> (radius km, titles to try in order)
PROPOSED = {
    'gulf': (600, ['Gulf of Mexico']),
    'ozarks': (600, ['Ozarks']),
    'idharriman': (30, ['Harriman State Park (Idaho)']),
    'nyharriman': (30, ['Harriman State Park (New York)', 'Harriman State Park']),
    'arvillagecreek': (30, ['Village Creek State Park (Arkansas)', 'Village Creek State Park']),
    'txvillagecreek': (30, ['Village Creek State Park (Texas)', 'Village Creek State Park (Lumberton, Texas)']),
}
OWNER_DECISION = ['sdponca']

def km(a, b):
    p = math.pi / 180; dl = (b[1] - a[1]) * p; x = math.sin((b[0] - a[0]) * p / 2) ** 2 + math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(x))

def article(title, get):
    """(canonical title, (lat, lon) or None, is_disambiguation) or None when the page does not exist."""
    q = 'https://en.wikipedia.org/w/api.php?action=query&prop=coordinates|pageprops&ppprop=disambiguation&coprimary=primary&redirects=1&format=json&titles=' + urllib.parse.quote(title)
    for p in ((get(q) or {}).get('query') or {}).get('pages', {}).values():
        if 'missing' in p or 'invalid' in p: return None
        c = (p.get('coordinates') or [None])[0]
        return p.get('title', title), (c['lat'], c['lon']) if c else None, 'disambiguation' in (p.get('pageprops') or {})
    return None

def load(data_dir):
    out = {}
    for f in sorted(os.listdir(data_dir)):
        if f.endswith('.json'):
            raw = open(os.path.join(data_dir, f), encoding='utf-8').read(); d = json.loads(raw); out[d['id']] = (os.path.join(data_dir, f), raw, d)
    return out

def run(data_dir, get, dry=False):
    """Returns (set [(id, old, new, km)], unresolved [(id, why)], owner_decision [id])."""
    places = load(data_dir); used = {}
    for pid, (_, _, d) in places.items():
        if d.get('imgwiki'): used.setdefault(d['imgwiki'], set()).add(pid)
    shared = {pid for t, ids in used.items() if len(ids) > 1 for pid in ids}   # decided before any change, so the order of the places does not matter
    done, unresolved = [], []
    for pid, (radius, titles) in PROPOSED.items():
        if pid not in places: continue
        f, raw, d = places[pid]; here = (d['lat'], d['lon']); why = []
        if pid not in shared: continue   # already has its own title
        for t in titles:
            a = article(t, get)
            if not a: why.append('%s: no such article' % t); continue
            canon, c, disamb = a
            if disamb: why.append('%s: disambiguation page' % canon); continue
            if not c: why.append('%s: no coordinates' % canon); continue
            dist = km(here, c)
            if dist > radius: why.append('%s: %.0f km from the place (limit %d)' % (canon, dist, radius)); continue
            if used.get(canon, set()) - {pid}: why.append('%s: already the title of %s' % (canon, ', '.join(sorted(used[canon] - {pid})))); continue
            old = d.get('imgwiki'); d['imgwiki'] = canon; used.setdefault(canon, set()).add(pid)
            if old: used[old].discard(pid)
            if not dry: open(f, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
            done.append((pid, old, canon, dist)); break
        else: unresolved.append((pid, '; '.join(why) or 'no candidate'))
    owner = [p for p in OWNER_DECISION if p in shared and len(used.get(places[p][2].get('imgwiki'), ())) > 1]
    return done, unresolved, owner

def main():
    import wm
    dry = '--dry' in sys.argv
    done, unresolved, owner = run(os.path.join(ROOT, 'data', 'places'), wm.get, dry)
    for pid, old, new, d in done: print('set %s: %s -> %s (%.1f km from the place)' % (pid, old, new, d))
    for pid, why in unresolved: print('unresolved %s: %s' % (pid, why))
    for pid in owner: print('owner-decision %s: shares its title with another place (a probable duplicate); not changed' % pid)
    print(len(done), 'titles', 'to set' if dry else 'set', '|', len(unresolved), 'unresolved |', len(owner), 'for the owner')
if __name__ == '__main__': main()
