#!/usr/bin/env python3
"""jobs/addabiotic.py (#1138): a place with no abiotic node gets the table's node and 'r' links to its users; a place that has one, a taken node id or a missing user is left alone or reported."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import addabiotic as AA
def w(root, rel, obj, **kw):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, **kw))
with tempfile.TemporaryDirectory() as r:
    for sid, cat in (('ab-soil', 'abiotic'), ('dc-fungi', 'decomp'), ('sp-a', None), ('sp-b', None)):
        o = {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'resource' if cat else 'taxon'}
        if cat: o['cat'] = cat
        w(r, 'data/species/rows/%s/%s.json' % (sid[:2], sid), o)
    w(r, 'data/places/p1.json', {'id': 'p1', 'nodes': [{'id': 'a', 'sp': 'sp-a'}, {'id': 'b', 'sp': 'sp-b'}, {'id': 'd', 'sp': 'dc-fungi'}], 'raw': [['a', 'b']]}, indent=1)
    w(r, 'data/places/p2.json', {'id': 'p2', 'nodes': [{'id': 'a', 'sp': 'sp-a'}, {'id': 'soil', 'sp': 'ab-soil'}], 'raw': []}, indent=1)
    t = {'p1': ('ab-soil', 'soil', 0.5, 'desc', ['a', 'b']), 'p2': ('ab-soil', 'soil', 0.5, 'desc', ['a'])}
    todo, bad = AA.plan(r, t)
    assert list(todo) == ['p1'] and not bad, (todo, bad)   # p2 already has an abiotic node
    AA.apply(r, todo)
    e = json.load(open(os.path.join(r, 'data/places/p1.json')))
    assert e['nodes'][-1] == {'id': 'soil', 'sp': 'ab-soil', 'xh': 0.5, 'desc': 'desc'} and e['raw'][-2:] == [['soil', 'a', 'r'], ['soil', 'b', 'r']]
    assert not AA.plan(r, t)[0]   # a second run adds nothing
    assert AA.plan(r, {'p3': ('ab-soil', 'x', 0.5, 'd', ['a'])})[1] == ['p3: no such place']
print('ok')
