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
    assert sorted(conv) == ['aa-bb', 'cc-dd', 'gg-hh', 'ii-jj'] and not bad, (conv, bad)   # same and change, a common-name page (keeps it) and an unresolved genus (Latin name); family page and species page are not converted
    assert conv['aa-bb'] == {'sid': 'aa', 'latin': 'Aa', 'name': 'Blue aa', 'wiki': 'Aa'} and conv['cc-dd']['name'] == 'Cc plant' and conv['cc-dd']['sid'] == 'cc'
    assert conv['gg-hh'] == {'sid': 'gg', 'latin': 'Gg', 'name': 'Common gg', 'wiki': 'Common gg'} and conv['ii-jj'] == {'sid': 'ii', 'latin': 'Ii', 'name': 'Ii', 'wiki': 'Ii'}
    assert 'ee-ff' in skip and 'kk' not in skip and 'gg-hh' not in skip and 'ii-jj' not in skip, skip
    RG.apply(r, conv); RG.record(r, conv, skip)
    a = rd(r, 'data/species/rows/aa/aa.json')
    assert (a['sid'], a['latin'], a['wiki'], a['name']) == ('aa', 'Aa', 'Aa', 'Blue aa') and a['desc'] == 'Blue aa (Aa): a plant.' and not os.path.exists(os.path.join(r, 'data/species/rows/aa/aa-bb.json'))
    assert [n['sp'] for n in rd(r, 'data/places/p1.json')['nodes']] == ['aa', 'cc', 'ii'] and open(os.path.join(r, 'data/places/p1.json')).read().startswith('{\n "id"')
    assert not os.path.exists(os.path.join(r, 'data/diets/aa/aa-bb.json')) and rd(r, 'data/diets/aa/aa.json') == {'sid': 'aa', 'prey': {'cc': {'k': 'e'}}}
    assert rd(r, 'data/diets/ii/ii.json') == {'sid': 'ii', 'prey': {'aa': {'k': 'e'}, 'cc': {'k': 'e'}}, 'pred': {'aa': {'k': 'e'}}}
    assert rd(r, 'data/species/taxonomy.json') == {} and rd(r, 'data/species/conservation.json') == {}
    assert rd(r, 'data/species/search_vocabulary.json')['also_called'] == {'aa': ['Old name', 'Aa bb'], 'cc': ['Cc dd'], 'gg': ['Gg hh'], 'ii': ['Ii jj']}, rd(r, 'data/species/search_vocabulary.json')
    assert rd(r, 'photos/species_pictures.json') == {'aa': {'f': 'abc.webp'}} and rd(r, 'photos/species_medium.json') == {'aa': 'abc.webp'} and rd(r, 'photos/species_missing.json') == {'cc': {'x': 1}} and rd(r, 'photos/species_tried.json') == {'cc': {'x': 1}}
    assert rd(r, 'data/audit/rowtitles.json')['rows']['cc'] == ['same', 'Cc plant', ''] and 'aa' in rd(r, 'data/audit/identity.json')['rows'] and 'aa-bb' not in rd(r, 'data/audit/identity.json')['rows']
    assert rd(r, 'data/audit/rowtogenus.json')['converted'] == {'aa-bb': ['aa', 'Blue aa'], 'cc-dd': ['cc', 'Cc plant'], 'gg-hh': ['gg', 'Common gg'], 'ii-jj': ['ii', 'Ii']}
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

# a genus row on a species page is repointed to the genus title; one already on its genus title is left
with tempfile.TemporaryDirectory() as r:
    build(r, [row('mm', 'Mm', 'Mm trees', 'Mm species'), row('nn', 'Nn', 'Nn trees', 'Nn')])
    i = rd(r, 'data/audit/identity.json'); i['rows']['mm'] = ['Q1', 'R2', 'Mm species', 'taxon', '']; i['rows']['nn'] = ['Q1', 'R2', 'Nn species', 'taxon', '']; w(r, 'data/audit/identity.json', i)
    assert RG.repoint(r) == {'kk': 'Kk', 'mm': 'Mm'} and rd(r, 'data/species/rows/mm/mm.json')['wiki'] == 'Mm species'
    RG.repoint(r, write=True)
    assert rd(r, 'data/species/rows/mm/mm.json')['wiki'] == 'Mm' and rd(r, 'data/species/rows/nn/nn.json')['wiki'] == 'Nn' and not RG.repoint(r)
print('ok repoint')

# --rename: a `latin` proposal renames a converted genus row (name and the start of desc); a name another row has is skipped
with tempfile.TemporaryDirectory() as r:
    build(r)
    cv = RG.plan(r)[0]; RG.apply(r, cv); RG.record(r, cv, {})
    t = rd(r, 'data/audit/rowtitles.json'); t['rows']['aa'] = ['latin', 'Aa', 'no common name']; t['rows']['cc'] = ['latin', 'Aa', 'no common name']; w(r, 'data/audit/rowtitles.json', t)
    out, sk = RG.latin_names(r)
    assert out == {'aa': ['Blue aa', 'Aa']} and list(sk) == ['cc'], (out, sk)
    RG.latin_names(r, write=True)
    a = rd(r, 'data/species/rows/aa/aa.json')
    assert a['name'] == 'Aa' and a['desc'] == 'Aa (Aa): a plant.' and rd(r, 'data/audit/rowtitles.json')['rows']['aa'] == ['same', 'Aa', '']
print('ok rename')

# --rename leaves a genus row whose page is a common-name title alone (owner: it keeps the common name)
with tempfile.TemporaryDirectory() as r:
    build(r)
    cv = RG.plan(r)[0]; RG.apply(r, cv); RG.record(r, cv, {})
    t = rd(r, 'data/audit/rowtitles.json'); t['rows']['gg'] = ['latin', 'Gg', 'no common name']; t['rows']['aa'] = ['latin', 'Aa', 'no common name']; w(r, 'data/audit/rowtitles.json', t)
    out, sk = RG.latin_names(r)
    assert 'gg' not in out and 'gg' in sk and 'common-name' in sk['gg'] and 'aa' in out, (out, sk)   # gg's page is "Common gg"
print('ok rename common')
