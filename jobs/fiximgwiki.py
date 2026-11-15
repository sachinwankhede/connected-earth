#!/usr/bin/env python3
"""fiximgwiki.py: give the places that share a Wikipedia title their own (#908; docs/DATA-PLAN.md).
Usage: fiximgwiki.py [--dry]   (run from the repository root; --dry lists and changes nothing). Host: en.wikipedia.org (already allowed), through jobs/wm.py.

Five titles are the `imgwiki` of ten places, so placepictures skips them (a picture keyed by title could land on the wrong place). Two of the ten carry a title that belongs to a different place
(`gulf`, the Northern Gulf of Mexico, has "Gulf Islands National Seashore"; `ozarks`, the Ozark habitat, has "Ozark National Scenic Riverways"), four are real parks that share a name across states
(Harriman, Village Creek), two keep the title they have (it is the right one), and `sdponca` looks like a duplicate of `neponca` (Ponca State Park lies wholly in Nebraska).
PROPOSED lists, for the six places that need one, the titles to try in order. A title is taken only when its article exists, is not a disambiguation page, has a primary coordinate within the place's
radius (30 km for a park, 600 km for a region), and no other place already uses it. Otherwise the place is left and listed `unresolved`. Only `imgwiki` is edited.
`sdponca` is a verified duplicate of `neponca` and is removed (owner decision 15 Nov): see DUPLICATES and remove_duplicates."""
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
OWNER_DECISION = []
# Owner decision 15 Nov (#908): a duplicate place is removed, but only after the job re-checks that it IS one: same name, within DUPLICATE_KM of the place that stays, and that place exists.
# Wikipedia puts Ponca State Park wholly in Nebraska, and `sdponca` (labelled South Dakota) sits 0.4 km from `neponca` with the same name and the same Wikipedia title.
DUPLICATES = {'sdponca': 'neponca'}
DUPLICATE_KM = 5

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

def remove_duplicates(root, dry=False):
    """Remove each place in DUPLICATES that is a verified duplicate of the one that stays: its file in data/places, its outline data/outlines/<id>.json and its entry in the place order (data/order/*.json; the validator needs both).
    Returns (removed [(id, kept, km)], refused [(id, why)]). Nothing else refers to a place by id except the outline and the order and what the build derives."""
    data_dir = os.path.join(root, 'data', 'places'); places = load(data_dir); removed, refused = [], []
    for pid, keep in DUPLICATES.items():
        if pid not in places: continue
        if keep not in places: refused.append((pid, '%s, the place that stays, does not exist' % keep)); continue
        a, b = places[pid][2], places[keep][2]; dist = km((a['lat'], a['lon']), (b['lat'], b['lon']))
        if a.get('name') != b.get('name'): refused.append((pid, 'name %r differs from %r' % (a.get('name'), b.get('name')))); continue
        if dist > DUPLICATE_KM: refused.append((pid, '%.1f km from %s (limit %d)' % (dist, keep, DUPLICATE_KM))); continue
        removed.append((pid, keep, dist))
        if dry: continue
        os.remove(places[pid][0]); ol = os.path.join(root, 'data', 'outlines', pid + '.json')
        if os.path.exists(ol): os.remove(ol)   # the outline file is named by the place id (the validator fails on an outline with no place)
        od = os.path.join(root, 'data', 'order')
        for f in sorted(os.listdir(od)) if os.path.isdir(od) else []:
            fp = os.path.join(od, f); raw = open(fp, encoding='utf-8').read()
            if f.endswith('.json') and pid in json.loads(raw):
                json.dump([i for i in json.loads(raw) if i != pid], open(fp, 'w', encoding='utf-8')); open(fp, 'a', encoding='utf-8').write('\n' if raw.endswith('\n') else '')
    return removed, refused

def main():
    import wm
    dry = '--dry' in sys.argv
    done, unresolved, owner = run(os.path.join(ROOT, 'data', 'places'), wm.get, dry)
    for pid, old, new, d in done: print('set %s: %s -> %s (%.1f km from the place)' % (pid, old, new, d))
    for pid, why in unresolved: print('unresolved %s: %s' % (pid, why))
    for pid in owner: print('owner-decision %s: shares its title with another place (a probable duplicate); not changed' % pid)
    removed, refused = remove_duplicates(ROOT, dry)
    for pid, keep, d in removed: print('remove %s: a duplicate of %s (same name, %.1f km apart)' % (pid, keep, d))
    for pid, why in refused: print('refused %s: %s' % (pid, why))
    print(len(done), 'titles', 'to set' if dry else 'set', '|', len(unresolved), 'unresolved |', len(owner), 'for the owner')
if __name__ == '__main__': main()
