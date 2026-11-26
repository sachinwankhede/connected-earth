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
    # a removal that would leave a place invalid keeps the row: the 10 species stay (the only abiotic node can go: validate.py warns)
    go, kept = SR.apply(r, {'bb-good', 'ab-soil', 'ss00-x', 'ss01-x', 'ss02-x'})
    assert go == ['ss01-x', 'ss02-x'] and set(kept) == {'bb-good', 'ss00-x', 'ab-soil'}, (go, kept)   # the only abiotic node stays (#1138: a place needs one); the 10-species minimum keeps two rows
    # a node whose only neighbour goes would be dropped with no links; if a journey ends at it, its row stays and so does the neighbour
    with tempfile.TemporaryDirectory() as r2:
        for sid in ('nb-bad', 'jj-jny') + tuple('tt%02d-x' % i for i in range(10)): w(r2, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
        for sid, cat in (('ab-soil', 'abiotic'), ('dc-fungi', 'decomp')): w(r2, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'resource', 'cat': cat})
        nd = [{'id': 'nb', 'sp': 'nb-bad'}, {'id': 'jj', 'sp': 'jj-jny'}, {'id': 'nab', 'sp': 'ab-soil'}, {'id': 'ndc', 'sp': 'dc-fungi'}] + [{'id': 'y%d' % i, 'sp': 'tt%02d-x' % i} for i in range(10)]
        rw = [['nb', 'jj'], ['nab', 'y0'], ['ndc', 'y0']] + [['y%d' % i, 'y0'] for i in range(1, 10)]
        w(r2, 'data/places/p2.json', {'id': 'p2', 'tip': {'id': 'y0'}, 'nodes': nd, 'raw': rw, 'ev': {}}, indent=1)
        w(r2, 'data/journeys/j.json', {'ends': [{'eco': 'p2', 'node': 'jj'}]})
        go, kept = SR.apply(r2, {'nb-bad'})
        assert go == [] and 'nb-bad' in kept, (go, kept)
        assert 'jj' in [n['id'] for n in json.load(open(os.path.join(r2, 'data/places/p2.json')))['nodes']]
    # a place a kept row blocks is removed whole, with its outline, picture and order entry; a place a journey names stays
    with tempfile.TemporaryDirectory() as r3:
        for sid in tuple('uu%02d-x' % i for i in range(10)) + ('tp-bad',): w(r3, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
        for sid, cat in (('ab-soil', 'abiotic'), ('dc-fungi', 'decomp')): w(r3, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'resource', 'cat': cat})
        def place(pid, species):   # `species` species nodes: a place with exactly 10 needs every one of them
            nd = [{'id': 'nab', 'sp': 'ab-soil'}, {'id': 'ndc', 'sp': 'dc-fungi'}] + [{'id': 'y%d' % i, 'sp': 'uu%02d-x' % i} for i in range(10)] + ([{'id': 'b', 'sp': 'tp-bad'}] if species == 11 else [])
            w(r3, 'data/places/%s.json' % pid, {'id': pid, 'tip': {'id': 'y0'}, 'nodes': nd, 'raw': [['nab', 'y0'], ['ndc', 'y0']] + [['y%d' % i, 'y0'] for i in range(1, 10)] + ([['b', 'y0']] if species == 11 else []), 'ev': {}})
            w(r3, 'data/outlines/%s.json' % pid, {'n': 1}); w(r3, 'photos/places/%s.jpg' % pid, 'x'); w(r3, 'photos/places-lg/%s.webp' % pid, 'x')
        place('pfine', 10)
        # pbad: 9 good species plus the bad one (10): removing the bad one leaves 9
        nd = [{'id': 'nab', 'sp': 'ab-soil'}, {'id': 'ndc', 'sp': 'dc-fungi'}, {'id': 'b', 'sp': 'tp-bad'}] + [{'id': 'y%d' % i, 'sp': 'uu%02d-x' % i} for i in range(9)]
        for pid in ('pbad', 'pjny'):
            w(r3, 'data/places/%s.json' % pid, {'id': pid, 'tip': {'id': 'y0'}, 'nodes': nd, 'raw': [['nab', 'y0'], ['ndc', 'y0'], ['b', 'y0']] + [['y%d' % i, 'y0'] for i in range(1, 9)], 'ev': {}})
            w(r3, 'data/outlines/%s.json' % pid, {'n': 1}); w(r3, 'photos/places/%s.jpg' % pid, 'x'); w(r3, 'photos/places-lg/%s.webp' % pid, 'x')
        w(r3, 'data/order/0000-main.json', ['pbad', 'pjny', 'pfine']); w(r3, 'data/journeys/j.json', {'ends': [{'eco': 'pjny', 'node': 'y1'}]})
        w(r3, 'photos/places/places.json', {'pbad': {'f': 'pbad.jpg'}, 'pfine': {'f': 'pfine.jpg'}}); w(r3, 'photos/places_large.json', {'pbad': 'pbad.webp'})
        SR.BATCHES['all'] = lambda ident: {'tp-bad': 'test'}
        gone, rows, kept = SR.run_places(r3, {})
        assert set(gone) == {'pbad'} and rows == [] and set(kept) == {'tp-bad'}, (gone, rows, kept)
        assert not os.path.exists(os.path.join(r3, 'data/places/pbad.json')) and not os.path.exists(os.path.join(r3, 'data/outlines/pbad.json')) and not os.path.exists(os.path.join(r3, 'photos/places/pbad.jpg')) and not os.path.exists(os.path.join(r3, 'photos/places-lg/pbad.webp'))
        assert os.path.exists(os.path.join(r3, 'data/places/pjny.json')) and os.path.exists(os.path.join(r3, 'data/places/pfine.json'))
        assert json.load(open(os.path.join(r3, 'data/order/0000-main.json'))) == ['pjny', 'pfine'] and list(json.load(open(os.path.join(r3, 'photos/places/places.json')))) == ['pfine'] and json.load(open(os.path.join(r3, 'photos/places_large.json'))) == {}
    # two orphan species nodes: dropping the first must not make the second look spare (the 10-species minimum holds)
    with tempfile.TemporaryDirectory() as r5:
        for sid in ('nn-bad',) + tuple('ww%02d-x' % i for i in range(11)): w(r5, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
        nd = [{'id': 'bad', 'sp': 'nn-bad'}] + [{'id': 'y%d' % i, 'sp': 'ww%02d-x' % i} for i in range(11)]   # y0 to y8 stay linked, y9 and y10 hang only on `bad`
        w(r5, 'data/places/p5.json', {'id': 'p5', 'nodes': nd, 'raw': [['y9', 'bad'], ['y10', 'bad']] + [['y%d' % i, 'y0'] for i in range(1, 9)], 'ev': {}})
        go, kept = SR.apply(r5, {'nn-bad'})
        n5 = [n for n in json.load(open(os.path.join(r5, 'data/places/p5.json')))['nodes'] if n['sp'].startswith('ww')]
        assert len(n5) >= 10, (go, kept, len(n5))
    # the opening tip is optional: removing the row a tip names removes the tip and keeps the place
    with tempfile.TemporaryDirectory() as r4:
        for sid in ('zz-bad',) + tuple('vv%02d-x' % i for i in range(10)): w(r4, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
        for sid, cat in (('ab-soil', 'abiotic'), ('dc-fungi', 'decomp')): w(r4, 'data/nodes/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'resource', 'cat': cat})
        nd = [{'id': 'z', 'sp': 'zz-bad'}, {'id': 'nab', 'sp': 'ab-soil'}, {'id': 'ndc', 'sp': 'dc-fungi'}] + [{'id': 'y%d' % i, 'sp': 'vv%02d-x' % i} for i in range(10)]
        w(r4, 'data/places/p4.json', {'id': 'p4', 'tip': {'id': 'z', 'title': 'Take away z'}, 'nodes': nd, 'raw': [['z', 'y0'], ['nab', 'y0'], ['ndc', 'y0']] + [['y%d' % i, 'y0'] for i in range(1, 10)], 'ev': {}})
        go, kept = SR.apply(r4, {'zz-bad'})
        e4 = json.load(open(os.path.join(r4, 'data/places/p4.json')))
        assert go == ['zz-bad'] and kept == {} and 'tip' not in e4 and 'z' not in [n['id'] for n in e4['nodes']] and len(e4['nodes']) == 12, (go, kept, e4)
# batch `unused`: a row no place node uses is listed; a row a place uses (including a journey's end node) is not
with tempfile.TemporaryDirectory() as r4:
    for sid in ('used-a', 'free-b', 'free-c'): w(r4, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'sk': 'taxon'})
    w(r4, 'data/places/p4.json', {'id': 'p4', 'nodes': [{'id': 'n', 'sp': 'used-a'}], 'raw': [], 'ev': {}})
    assert SR.batch_unused({}, r4) == {'free-b': 'no place uses it', 'free-c': 'no place uses it'}
print('strictrows ok')
