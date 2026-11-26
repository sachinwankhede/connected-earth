#!/usr/bin/env python3
"""jobs/mergerows.py (#1061): nodes move to the winner; a place with both keeps the winner's node and the loser's edges move to it; node text is kept."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import mergerows as M
def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, indent=1))
with tempfile.TemporaryDirectory() as r:
    for sid, desc in (('lose', 'loser text'), ('win', 'winner text')): w(r, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'name': sid, 'latin': '', 'sk': 'resource', 'cat': 'abiotic', 'desc': desc})
    w(r, 'data/species/rows/sp/sp-a.json', {'sid': 'sp-a', 'name': 'A', 'latin': 'Aus a', 'sk': 'taxon'})
    w(r, 'data/places/p1.json', {'id': 'p1', 'nodes': [{'id': 'a', 'sp': 'sp-a'}, {'id': 'l', 'sp': 'lose'}], 'raw': [['l', 'a', 'r']], 'ev': {}})
    w(r, 'data/places/p2.json', {'id': 'p2', 'nodes': [{'id': 'a', 'sp': 'sp-a'}, {'id': 'l', 'sp': 'lose'}, {'id': 'w', 'sp': 'win'}], 'raw': [['l', 'a', 'r'], ['w', 'a', 'r']], 'ev': {}})
    M.merge(r, {'lose': 'win'})
    p1 = json.load(open(os.path.join(r, 'data/places/p1.json'))); p2 = json.load(open(os.path.join(r, 'data/places/p2.json')))
    assert p1['nodes'][1]['sp'] == 'win' and p1['nodes'][1]['desc'] == 'loser text', p1   # moved, kept its text
    assert [n['id'] for n in p2['nodes']] == ['a', 'w'] and p2['raw'] == [['w', 'a', 'r']], p2   # one node, edges deduplicated
    assert not os.path.exists(os.path.join(r, 'data/nodes/rows/lo/lose.json'))
print('ok')
