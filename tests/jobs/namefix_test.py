#!/usr/bin/env python3
"""jobs/namefix.py: a taxon row whose page is about exactly that taxon (or one species) is renamed to the page title; a row whose page is something broader is listed for removal; groups are never renamed."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import namefix as NF
def w(root, rel, obj): p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(obj, indent=1))
with tempfile.TemporaryDirectory() as r:
    rows = {'sx-sal': {'latin': 'Salix', 'name': 'Willows', 'wiki': 'Willow', 'sk': 'taxon'}, 'sx-owl': {'latin': 'Asio flammeus', 'name': 'Pueo (short-eared owl)', 'wiki': 'Short-eared owl', 'sk': 'taxon'},
            'sx-loc': {'latin': 'Acanthacris ruficornis', 'name': 'Garden locust', 'wiki': 'Locust', 'sk': 'taxon'}, 'sx-grp': {'latin': 'Arenaria', 'name': 'Migratory shorebirds', 'wiki': 'Ruddy turnstone', 'sk': 'group'},
            'sx-ok': {'latin': 'Acer rubrum', 'name': 'Red maple', 'wiki': 'Red maple', 'sk': 'taxon'}}
    for sid, d in rows.items(): d['sid'] = sid; w(r, 'data/species/rows/%s/%s.json' % (sid[:2], sid), d)
    w(r, 'data/audit/rowtitles.json', {'rows': {'sx-sal': ['change', 'Willow', ''], 'sx-owl': ['change', 'Short-eared owl', ''], 'sx-loc': ['change', 'Locust', ''], 'sx-grp': ['change', 'Ruddy turnstone', ''], 'sx-ok': ['same', 'Red maple', '']}})
    w(r, 'data/audit/identity.json', {'ranks': {'Q1': 'genus', 'Q2': 'species'}, 'rows': {'sx-sal': ['Q10', 'Q1', 'Salix', 'taxon', ''], 'sx-owl': ['Q11', 'Q2', 'Asio flammeus', 'taxon', ''], 'sx-loc': ['Q12', '', '', 'taxon', ''], 'sx-grp': ['Q13', 'Q2', 'Calidris', 'group', ''], 'sx-ok': ['Q14', 'Q2', 'Acer rubrum', 'taxon', '']}})
    ren, dele = NF.lists(r)
    assert ren == {'sx-sal': 'Willow', 'sx-owl': 'Short-eared owl'}, ren
    assert set(dele) == {'sx-loc', 'sx-grp'}, dele
    done = NF.rename(r, ren)
    assert [(a, c) for a, _, c in done] == [('sx-owl', 'Short-eared owl'), ('sx-sal', 'Willow')]
    assert json.load(open(os.path.join(r, 'data/species/rows/sx/sx-owl.json')))['name'] == 'Short-eared owl' and json.load(open(os.path.join(r, 'data/species/rows/sx/sx-loc.json')))['name'] == 'Garden locust'
# rows that share one name: the genus row, else the most used row, keeps it; the others take their page title (a scientific name); nothing is removed
with tempfile.TemporaryDirectory() as r:
    for sid, lat, nm in (('mm-gen', 'Macaranga', 'Macaranga'), ('mm-sp', 'Macaranga tanarius', 'Macaranga'), ('rr-a', 'Rosa a', 'Wild rose'), ('rr-b', 'Rosa b', 'Wild rose'), ('rr-c', 'Rosa c', 'Wild rose')):
        w(r, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': lat, 'name': nm, 'wiki': lat, 'sk': 'taxon'})
    w(r, 'data/places/p.json', {'nodes': [{'id': 'n1', 'sp': 'rr-b'}, {'id': 'n2', 'sp': 'rr-b'}, {'id': 'n3', 'sp': 'rr-a'}, {'id': 'n4', 'sp': 'mm-sp'}]})
    assert NF.shared(r) == {'mm-sp': 'Macaranga tanarius', 'rr-a': 'Rosa a', 'rr-c': 'Rosa c'}, NF.shared(r)
print('namefix ok')
