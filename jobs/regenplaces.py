#!/usr/bin/env python3
"""regenplaces.py id1,id2,...: rebuild the food web (nodes, raw, ev, tip) of automatic places at the place's CURRENT location (#863).
Why: the species of an automatic place are the ones most often recorded in GBIF near its stored location. #767 moved the pin of places that were built at a wrong point, so their species
(and so their food web) belong to the old point. Each place is turned back into the park record the draft step reads (id, name, state, kind, centre, radius from its own notes), then the same
steps as the first build run (draft.py, autogen.py, names.py, autogen.py). Everything else on the place (name, location, photo, sources, notes, story) is kept.
Writes regenplaces.md (a before/after table for the pull request body) and regenplaces.json ({'ids': [...]}). A place that is not automatic, has several states or lost its radius is skipped and listed."""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def park_from_place(d):
    """The park record draft.py and autogen.py read, rebuilt from a place file, or (None, reason) when the place cannot be rebuilt this way."""
    if not d.get('auto'): return None, 'not an automatic place'
    names = [x for x in (d.get('place') or '').rsplit(', USA', 1)[0].split(', ') if x]
    if len(d.get('states') or []) != 1 or not names: return None, 'not exactly one state'
    m = re.search(r'within about ([0-9.]+) km', d.get('notes') or '')
    if not m: return None, 'no radius in its notes'
    return dict(id=d['id'], name=d['name'], short=d['short'], states=[names[-1]], kind=d['kind'], lat=d['lat'], lon=d['lon'], radius=float(m.group(1)), points=None), None

def species_names(d):
    return [n.get('name') or n.get('sp') for n in d['nodes'] if not n.get('cat')]

def run(cmd, env):
    print('$', ' '.join(cmd), flush=True)
    if subprocess.run(cmd, cwd=ROOT, env=dict(os.environ, **env)).returncode: sys.exit('step failed: ' + ' '.join(cmd))

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'build')); import species
    ids = [i.strip() for i in sys.argv[1].split(',') if i.strip()]
    parks, skipped, before = [], [], {}
    for i in ids:
        f = os.path.join(ROOT, 'data', 'places', i + '.json')
        if not os.path.exists(f): skipped.append((i, 'no such place')); continue
        d = json.load(open(f)); p, why = park_from_place(d)
        if not p: skipped.append((i, why)); continue
        parks.append(p); before[i] = species_names(species.load(f))
    work = os.path.join(ROOT, 'jobs', 'work', 'regenplaces'); os.makedirs(work, exist_ok=True)
    json.dump(parks, open(os.path.join(work, 'parks.json'), 'w'), indent=1)
    env = {'WORK': work}
    if parks:
        for _ in range(3): run(['python3', 'jobs/draft.py', 'all'], env)   # a GBIF call that failed is not cached, so a second and third pass fill the gaps (the first run came back with no plants for 6 of 15 places)
        run(['python3', 'jobs/autogen.py'], env)
        run(['python3', 'jobs/names.py', '--from-data', os.path.join(work, 'out')], env); run(['python3', 'jobs/autogen.py'], env)
    rows, done = [], []
    for p in parks:
        i = p['id']; out = os.path.join(work, 'out', i + '.json')
        if not os.path.exists(out): rows.append((p['name'], before[i], None)); continue
        new = json.load(open(out)); f = os.path.join(ROOT, 'data', 'places', i + '.json'); old = json.load(open(f))
        for k in ('nodes', 'raw', 'ev'): old[k] = new[k]
        old['tip'] = new.get('tip')
        json.dump(old, open(f, 'w'), ensure_ascii=False)
        rows.append((p['name'], before[i], species_names(species.load(f)))); done.append(i)
    with open(os.path.join(ROOT, 'regenplaces.md'), 'w') as f:
        f.write('Food webs rebuilt at the corrected location for %d places (#863). The species before and after are the first eight of each.\n\n| Place | Species before | Species after |\n|---|---|---|\n' % len(done))
        for name, b, a in rows: f.write('| %s | %s | %s |\n' % (name, ', '.join(b[:8]), ', '.join(a[:8]) if a else 'not rebuilt (too few species or no data)'))
        for i, why in skipped: f.write('\nSkipped %s: %s.' % (i, why))
    json.dump({'ids': done}, open(os.path.join(ROOT, 'regenplaces.json'), 'w'))
    print(open(os.path.join(ROOT, 'regenplaces.md')).read())
