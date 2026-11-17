#!/usr/bin/env python3
"""Every species row the app lists carries its species id as the last value and no Latin name (#1008): the Species tab files (api/species-tab[-pilot]/*.json, rows [usual name, places,
picture or 0, id]) and the species page's "What it eats", "What eats it" and "Related species" rows (api/species/<id>.json: ea, eb, rl). The id is the slug of the Latin name; the app shows
the usual name and opens the species by the id, so the Latin name in a row would only cost bytes. The id of a row whose species has a file is the file's own name."""
import json, os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species

SID = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
files = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, 'api', 'species', '*.json'))}

def check(where, r, seen):
    assert len(r) == 4 and isinstance(r[0], str) and isinstance(r[1], int) and (r[2] == 0 or isinstance(r[2], str)) and isinstance(r[3], str) and SID.match(r[3]), '%s: %r is not [usual name, places, picture or 0, species id]' % (where, r)
    seen.append(r[3])

tabs = [f for d in ('species-tab', 'species-tab-pilot') for f in glob.glob(os.path.join(ROOT, 'api', d, '*.json'))]
if not tabs: print('ok (the build has not run)'); sys.exit(0)
n = 0
for f in tabs:
    name = os.path.basename(f)
    if name == 'groups.json' or name.startswith('o-'): continue   # groups and orders are lists of groups, not species rows
    seen = []
    for r in json.load(open(f)): check(f, r, seen); n += 1
    assert len(seen) == len(set(seen)), f + ': a species twice in one page'
m = linked = 0
for f in glob.glob(os.path.join(ROOT, 'api', 'species', '*.json')):
    d = json.load(open(f))
    assert species.slug(d['l']) == os.path.basename(f)[:-5], f + ': the file is named by the species id'
    for k in ('ea', 'eb', 'rl'):
        seen = []
        for r in d.get(k, []): check('%s %s' % (f, k), r, seen); m += 1
assert n > 1000 and m > 1000, (n, m)
print('ok (%d tab rows, %d diet and related rows)' % (n, m))
