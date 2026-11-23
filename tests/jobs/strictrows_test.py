#!/usr/bin/env python3
"""jobs/strictrows.py: removing a row takes its node, its edge records, its diet file and entries, and its taxonomy entry; a row whose node ends a journey is kept; the layout of each file is kept."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import strictrows as SR
def w(root, rel, obj, **kw):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, **kw))
with tempfile.TemporaryDirectory() as r:
    for sid in ('aa-bad', 'bb-good', 'cc-jny') + tuple('ss%02d-x' % i for i in range(10)): w(r, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
    for sid, cat in (('ab-soil', 'abiotic'), ('dc-fungi', 'decomp')): w(r, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'resource', 'cat': cat})
    nodes = [{'id': 'n1', 'sp': 'aa-bad'}, {'id': 'n2', 'sp': 'bb-good'}, {'id': 'n3', 'sp': 'cc-jny'}, {'id': 'nab', 'sp': 'ab-soil'}, {'id': 'ndc', 'sp': 'dc-fungi'}] + [{'id': 'x%d' % i, 'sp': 'ss%02d-x' % i} for i in range(10)]
    raw = [['n1', 'n2'], ['n2', 'n3'], ['n3', 'n2', 'r'], ['nab', 'n2', 'r'], ['ndc', 'n2', 'r']] + [['x%d' % i, 'n2'] for i in range(10)]
    w(r, 'data/places/p1.json', {'id': 'p1', 'tip': {'id': 'n2'}, 'nodes': nodes, 'raw': raw, 'ev': {'n1>n2': ['x'], 'n2>n3': ['y']}}, indent=1)
    w(r, 'data/journeys/j.json', {'ends': [{'eco': 'p1', 'node': 'n3'}]})
    w(r, 'data/diets/bb/bb-good.json', {'sid': 'bb-good', 'prey': {'aa-bad': {'k': 'e'}, 'cc-jny': {'k': 'e'}}}, separators=(',', ':'))
    w(r, 'data/diets/aa/aa-bad.json', {'sid': 'aa-bad', 'prey': {'bb-good': {'k': 'e'}}}, separators=(',', ':'))
    w(r, 'data/species/taxonomy.json', {'aa-bad': {'a': 1}, 'bb-good': {'a': 2}}, separators=(',', ':'))
    w(r, 'data/species/conservation_asked.json', ['aa-bad', 'bb-good'], separators=(',', ':'))
    go, kept = SR.apply(r, {'aa-bad', 'cc-jny'})
    assert go == ['aa-bad'] and list(kept) == ['cc-jny'], (go, kept)
    pl = json.load(open(os.path.join(r, 'data/places/p1.json')))
    assert 'n1' not in [n['id'] for n in pl['nodes']] and len(pl['nodes']) == 14 and ['n1', 'n2'] not in pl['raw'] and ['n2', 'n3'] in pl['raw'] and list(pl['ev']) == ['n2>n3'], pl
    assert open(os.path.join(r, 'data/places/p1.json')).read().startswith('{\n "id"'), 'layout kept'
    assert not os.path.exists(os.path.join(r, 'data/species/rows/aa/aa-bad.json')) and os.path.exists(os.path.join(r, 'data/species/rows/cc/cc-jny.json'))
    assert not os.path.exists(os.path.join(r, 'data/diets/aa/aa-bad.json'))
    assert json.load(open(os.path.join(r, 'data/diets/bb/bb-good.json')))['prey'] == {'cc-jny': {'k': 'e'}}
    assert json.load(open(os.path.join(r, 'data/species/taxonomy.json'))) == {'bb-good': {'a': 2}} and json.load(open(os.path.join(r, 'data/species/conservation_asked.json'))) == ['bb-good']
    # a removal that would leave a place invalid keeps the row: the tip, the only abiotic node and the 10 species stay
    go, kept = SR.apply(r, {'bb-good', 'ab-soil', 'ss00-x', 'ss01-x', 'ss02-x'})
    assert go == ['ss01-x', 'ss02-x'] and set(kept) == {'bb-good', 'ab-soil', 'ss00-x'}, (go, kept)
print('strictrows ok')
