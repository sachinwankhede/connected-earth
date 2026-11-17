#!/usr/bin/env python3
"""build/validate_api.py fails a place file whose node lacks its id (#1008): a species node (Latin name, no cat) needs sid, a concept node (cat and a wiki title) needs nid."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import validate_api

assert validate_api.nodes_missing_ids({'nodes': [{'id': 'wolf', 'latin': 'Canis lupus', 'sid': 'canis-lupus'}, {'id': 'sun', 'cat': 'abiotic', 'wiki': 'Sunlight', 'nid': 'sunlight'}]}) == []
assert validate_api.nodes_missing_ids({'nodes': [{'id': 'wolf', 'latin': 'Canis lupus'}]}) == ['wolf']
assert validate_api.nodes_missing_ids({'nodes': [{'id': 'sun', 'cat': 'abiotic', 'wiki': 'Sunlight'}]}) == ['sun']
assert validate_api.nodes_missing_ids({'nodes': [{'id': 'x', 'cat': 'abiotic'}]}) == [], 'a concept node without a title has no nid'
assert validate_api.nodes_missing_ids({}) == []
with tempfile.TemporaryDirectory() as d:
    json.dump({'nodes': [{'id': 'wolf', 'latin': 'Canis lupus'}]}, open(os.path.join(d, 'yellowstone.json'), 'w'))
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'validate_api.py'), d], capture_output=True, text=True)
    assert r.returncode == 1 and 'yellowstone.json' in r.stdout and 'wolf' in r.stdout, r.stdout + r.stderr
with tempfile.TemporaryDirectory() as d:   # the built cards leave out `imgwiki` (the app never reads it, #1008)
    os.makedirs(os.path.join(d, 'places', 'main'))
    json.dump({'a': {'name': 'A', 'place': 'p', 'blurb': 'b', 'imgwiki': 'A', 'idx': {}}}, open(os.path.join(d, 'places', 'main', 'cards-world.json'), 'w'))
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'validate_api.py'), d], capture_output=True, text=True)
    assert r.returncode == 1 and 'cards-world.json' in r.stdout, r.stdout + r.stderr
print('ok')
