#!/usr/bin/env python3
"""Every node of a built place file carries the id of its species (sid) or concept (nid), so the app works out no id from a name (#973):
a species node (a Latin name, no cat) has sid = the species id, a concept node (cat and a wiki title) has nid = the node id, and no node has the wrong kind of id."""
import json, os, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import node_photos, species

files = [f for f in glob.glob(os.path.join(ROOT, 'api', '*.json')) if os.path.basename(f) != 'species-pictures.json']
if not files: print('ok (the build has not run)'); sys.exit(0)
n_sid = n_nid = 0
for f in files:
    for n in json.load(open(f)).get('nodes', []):
        who = '%s:%s' % (os.path.basename(f), n.get('id'))
        if n.get('latin') and not n.get('cat'):
            assert n.get('sid') == species.slug(n['latin']), who + ': a species node has its species id'; n_sid += 1
        else: assert 'sid' not in n, who + ': only a species node has a sid'
        if n.get('cat') and n.get('wiki'):
            assert n.get('nid') == node_photos.node_id(n['wiki']), who + ': a concept node has its node id'; n_nid += 1
        else: assert 'nid' not in n, who + ': only a concept node with a title has a nid'
assert n_sid > 1000 and n_nid > 100, (n_sid, n_nid)
print('ok (%d species nodes, %d concept nodes in %d files)' % (n_sid, n_nid, len(files)))
