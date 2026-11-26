#!/usr/bin/env python3
"""jobs/rowtogenus.py (#1142): a species row whose page is a genus becomes the genus row; nodes, diets, vocabulary, picture and audit files follow; collisions stop it; skipped rows are listed; species_photos.rekey moves list entries."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import rowtogenus as RG
from species_photos import SpeciesPhotos
def w(root, rel, obj, **kw):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, **kw))
def rd(root, rel): return json.load(open(os.path.join(root, rel)))
def row(sid, latin, name, wiki): return {'sid': sid, 'latin': latin, 'name': name, 'wiki': wiki, 'sk': 'taxon', 'tl': 1, 'desc': '%s (%s): a plant.' % (name, latin)}

def build(r, extra=()):
    rows = [row('aa-bb', 'Aa bb', 'Blue aa', 'Aa bb'), row('cc-dd', 'Cc dd', 'Cc', 'Cc dd'), row('ee-ff', 'Ee ff', 'Ee ff', 'Ee ff'), row('gg-hh', 'Gg hh', 'Common gg', 'Common gg'), row('ii-jj', 'Ii jj', 'Ij', 'Ii jj'), row('kk', 'Kk', 'Kk plant', 'Kk plant')] + list(extra)
    for x in rows: w(r, 'data/species/rows/%s/%s.json' % (x['sid'][:2], x['sid']), x, indent=1)
    q = lambda t, rank: ['Q1', rank, t, 'taxon', '']
    w(r, 'data/audit/identity.json', {'ranks': {'R1': 'genus', 'R2': 'species', 'R3': 'family'}, 'rows': {'aa-bb': q('Aa', 'R1'), 'cc-dd': q('Cc', 'R1'), 'ee-ff': q('Ee', 'R3'), 'gg-hh': q('Gg', 'R1'), 'ii-jj': q('Ii', 'R1'), 'kk': q('Kk', 'R2')}})
    w(r, 'data/audit/rowtitles.json', {'rows': {'aa-bb': ['same', 'Blue aa', ''], 'cc-dd': ['change', 'Cc plant', ''], 'ee-ff': ['same', 'Ee ff', ''], 'gg-hh': ['same', 'x', ''], 'ii-jj': ['unresolved', '', ''], 'kk': ['same', 'Kk plant', '']}})
    w(r, 'data/places/p1.json', {'id': 'p1', 'nodes': [{'id': 'n1', 'sp': 'aa-bb'}, {'id': 'n2', 'sp': 'cc-dd'}, {'id': 'n3', 'sp': 'ii-jj'}], 'raw': [['n1', 'n2']]}, indent=1)
    w(r, 'data/diets/aa/aa-bb.json', {'sid': 'aa-bb', 'prey': {'cc-dd': {'k': 'e'}}}, separators=(',', ':'))
    w(r, 'data/diets/ii/ii-jj.json', {'sid': 'ii-jj', 'prey': {'aa-bb': {'k': 'e'}, 'cc-dd': {'k': 'e'}}, 'pred': {'aa-bb': {'k': 'e'}}}, separators=(',', ':'))
    w(r, 'data/species/taxonomy.json', {'aa-bb': {'a': 1}, 'ii-jj': {'a': 2}}, separators=(',', ':'))
    w(r, 'data/species/conservation.json', {'cc-dd': {'a': 1}}, separators=(',', ':'))
    w(r, 'data/species/search_vocabulary.json', {'also_called': {'aa-bb': ['Old name']}}, separators=(',', ':'))
    for n in ('species_pictures', 'species_medium', 'species_large'): w(r, 'photos/%s.json' % n, {'aa-bb': {'f': 'abc.webp'}} if n == 'species_pictures' else {'aa-bb': 'abc.webp'}, indent=0, sort_keys=True)
    for n in ('species_missing', 'species_tried'): w(r, 'photos/%s.json' % n, {'cc-dd': {'x': 1}}, indent=0, sort_keys=True)

with tempfile.TemporaryDirectory() as r:
    build(r)
    conv, skip, bad = RG.plan(r)
    assert sorted(conv) == ['aa-bb', 'cc-dd'] and not bad, (conv, bad)   # same and change; family page, common-name page, unresolved and species page are not converted
    assert conv['aa-bb'] == {'sid': 'aa', 'latin': 'Aa', 'name': 'Blue aa', 'wiki': 'Aa'} and conv['cc-dd']['name'] == 'Cc plant' and conv['cc-dd']['sid'] == 'cc'
    assert 'gg-hh' in skip and 'common-name' in skip['gg-hh'] and 'ii-jj' in skip and 'unresolved' in skip['ii-jj'] and 'ee-ff' in skip and 'kk' not in skip, skip
    RG.apply(r, conv); RG.record(r, conv, skip)
    a = rd(r, 'data/species/rows/aa/aa.json')
    assert (a['sid'], a['latin'], a['wiki'], a['name']) == ('aa', 'Aa', 'Aa', 'Blue aa') and a['desc'] == 'Blue aa (Aa): a plant.' and not os.path.exists(os.path.join(r, 'data/species/rows/aa/aa-bb.json'))
    assert [n['sp'] for n in rd(r, 'data/places/p1.json')['nodes']] == ['aa', 'cc', 'ii-jj'] and open(os.path.join(r, 'data/places/p1.json')).read().startswith('{\n "id"')
    assert not os.path.exists(os.path.join(r, 'data/diets/aa/aa-bb.json')) and rd(r, 'data/diets/aa/aa.json') == {'sid': 'aa', 'prey': {'cc': {'k': 'e'}}}
    assert rd(r, 'data/diets/ii/ii-jj.json') == {'sid': 'ii-jj', 'prey': {'aa': {'k': 'e'}, 'cc': {'k': 'e'}}, 'pred': {'aa': {'k': 'e'}}}
    assert rd(r, 'data/species/taxonomy.json') == {'ii-jj': {'a': 2}} and rd(r, 'data/species/conservation.json') == {}
    assert rd(r, 'data/species/search_vocabulary.json')['also_called'] == {'aa': ['Old name', 'Aa bb'], 'cc': ['Cc dd']}, rd(r, 'data/species/search_vocabulary.json')
    assert rd(r, 'photos/species_pictures.json') == {'aa': {'f': 'abc.webp'}} and rd(r, 'photos/species_medium.json') == {'aa': 'abc.webp'} and rd(r, 'photos/species_missing.json') == {'cc': {'x': 1}} and rd(r, 'photos/species_tried.json') == {'cc': {'x': 1}}
    assert rd(r, 'data/audit/rowtitles.json')['rows']['cc'] == ['same', 'Cc plant', ''] and 'aa' in rd(r, 'data/audit/identity.json')['rows'] and 'aa-bb' not in rd(r, 'data/audit/identity.json')['rows']
    assert rd(r, 'data/audit/rowtogenus.json')['converted'] == {'aa-bb': ['aa', 'Blue aa'], 'cc-dd': ['cc', 'Cc plant']}
    c2, s2, b2 = RG.plan(r)   # a second run has nothing left to convert
    assert not c2 and not b2

# collisions: a row already on the genus id, two rows on one genus, a name another row has
with tempfile.TemporaryDirectory() as r:
    build(r, [row('aa', 'Aa', 'Aa genus', 'Aa')])
    assert any('already exists' in q for q in RG.plan(r)[2])
with tempfile.TemporaryDirectory() as r:
    build(r, [row('aa-cc', 'Aa cc', 'Other', 'Aa cc')])
    i = rd(r, 'data/audit/identity.json'); i['rows']['aa-cc'] = ['Q1', 'R1', 'Aa', 'taxon', '']; w(r, 'data/audit/identity.json', i)
    t = rd(r, 'data/audit/rowtitles.json'); t['rows']['aa-cc'] = ['same', 'Other', '']; w(r, 'data/audit/rowtitles.json', t)
    assert any('both become aa' in q for q in RG.plan(r)[2])
with tempfile.TemporaryDirectory() as r:
    build(r, [row('zz-yy', 'Zz yy', 'Cc plant', 'Zz yy')])
    assert any('already row zz-yy' in q for q in RG.plan(r)[2])

# SpeciesPhotos.rekey moves every list entry
with tempfile.TemporaryDirectory() as r:
    build(r); s = SpeciesPhotos(r); s.rekey('aa-bb', 'aa'); s.rekey('cc-dd', 'cc')
    assert 'aa' in s.pics and 'aa-bb' not in s.pics and 'aa' in s.medium and 'aa' in s.large and 'cc' in s.miss_ and 'cc' in s.tried
print('ok')
