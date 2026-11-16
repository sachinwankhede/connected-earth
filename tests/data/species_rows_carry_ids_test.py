#!/usr/bin/env python3
"""Every species row the app lists carries its species id as the fifth value (#1008): the Species tab files (api/species-tab[-pilot]/*.json, rows [latin, name, places, picture or 0, id])
and the species page's "What it eats", "What eats it" and "Related species" rows (api/species/<id>.json: ea, eb, rl). The id is the slug of the Latin name, so the app opens a species by it and works nothing out from the name."""
import json, os, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species

def rows_of(x):
    if isinstance(x, list) and x and isinstance(x[0], list) and len(x[0]) >= 4 and isinstance(x[0][2], int) and isinstance(x[0][1], str) and isinstance(x[0][0], str): return x
    return []

tabs = [f for d in ('species-tab', 'species-tab-pilot') for f in glob.glob(os.path.join(ROOT, 'api', d, '*.json'))]
if not tabs: print('ok (the build has not run)'); sys.exit(0)
n = 0
for f in tabs:
    name = os.path.basename(f)
    if name == 'groups.json' or name.startswith('o-'): continue   # groups and orders are lists of groups, not species rows
    for r in json.load(open(f)):
        assert len(r) == 5 and r[4] == species.slug(r[0]), '%s: %r is not [latin, name, places, picture, species id]' % (f, r); n += 1
m = 0
for f in glob.glob(os.path.join(ROOT, 'api', 'species', '*.json')):
    d = json.load(open(f))
    for k in ('ea', 'eb', 'rl'):
        for r in d.get(k, []):
            assert len(r) == 5 and r[4] == species.slug(r[0]), '%s %s: %r has no species id' % (f, k, r); m += 1
assert n > 1000 and m > 1000, (n, m)
print('ok (%d tab rows, %d diet and related rows)' % (n, m))
