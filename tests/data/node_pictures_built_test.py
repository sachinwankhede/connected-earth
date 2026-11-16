#!/usr/bin/env python3
"""#976 step B: a built place file lists the picture of each non-species node under node:<id> (the slug of its concept title), the entry matches its record in
photos/node_pictures.json, its credit has only a, l, lu, p, and the picture file is published with the app. Runs on the built site; skipped when the build or the records are not there."""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rec = os.path.join(ROOT, 'photos', 'node_pictures.json')
if not os.path.exists(rec) or not glob.glob(os.path.join(ROOT, 'api', '*.json')):
    print('skipped: no node records or the build has not run'); sys.exit(0)
pics = json.load(open(rec)); n = 0; seen = set()
for f in glob.glob(os.path.join(ROOT, 'api', '*.json')):
    w = json.load(open(f))
    if 'nodes' not in w: continue
    ph = w.get('ph') or {}; phm = w.get('phm') or {}
    for node in w['nodes']:
        if not (node.get('cat') and node.get('wiki')): continue
        nid = re.sub(r'[^a-z0-9]+', '-', node['wiki'].lower()).strip('-')
        key = 'node:' + nid
        if nid in pics:
            assert key in ph, '%s: node %s has a record but the place file has no %s' % (os.path.basename(f), node['id'], key)
            assert ph[key][0] == pics[nid]['f'], (f, key)
            assert set(phm.get(key, {})) <= {'a', 'l', 'lu', 'p'}, (f, key, phm.get(key))
            assert os.path.exists(os.path.join(ROOT, 'photos', 'nodes', pics[nid]['f'])), pics[nid]['f']
            n += 1; seen.add(nid)
        else:
            assert key not in ph, '%s: %s has no record' % (os.path.basename(f), key)
assert n and seen, 'no place carries a node picture'
print('ok', n, 'node entries,', len(seen), 'concepts')
