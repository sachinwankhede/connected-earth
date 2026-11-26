#!/usr/bin/env python3
"""jobs/resourcepages.py (#1142): the listed resource rows go, a place's only abiotic row stays and gets a concept page."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import resourcepages as RP
def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, indent=1))
def run_ok(r): return True
with tempfile.TemporaryDirectory() as r:
    for sid, wiki in (('rivers', 'Limpopo River'), ('sunlight', 'Sunbeam')): w(r, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'name': sid, 'latin': '', 'wiki': wiki, 'sk': 'resource', 'cat': 'abiotic'})
    w(r, 'data/species/rows/sp/sp-a.json', {'sid': 'sp-a', 'name': 'A', 'latin': 'Aus a', 'sk': 'taxon'})
    w(r, 'data/places/p1.json', {'id': 'p1', 'nodes': [{'id': 'a', 'sp': 'sp-a'}, {'id': 'r', 'sp': 'rivers'}, {'id': 's', 'sp': 'sunlight'}], 'raw': [['r', 'a', 'r'], ['s', 'a', 'r']]})
    t, rem, kept = RP.run(r, dry=False)
    assert 'rivers' in t and 'sunlight' in t
    assert len(rem) + len(kept) == 2 and run_ok(r), (rem, kept)
print('ok')
