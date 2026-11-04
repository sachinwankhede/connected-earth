#!/usr/bin/env python3
"""geoids: ids and names of countries and states in a place file (#251). Run: python3 tests/data/geoids_test.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import geoids

def test_ids_and_names_give_the_same_place():
    by_name = geoids.names({'country': 'United States of America', 'cont': 'North America', 'states': ['Missouri']})
    by_id = geoids.names({'country': geoids.country_id('United States of America'), 'states': [geoids.state_id('Missouri')]})
    assert by_name == by_id, (by_name, by_id)
    assert by_id['cont'] == 'North America' and by_id['states'] == ['Missouri']

def test_countries_list_and_unknown_values():
    e = geoids.names({'country': '392', 'countries': ['392', 'Russia']})
    assert e['country'] == 'Japan' and e['countries'] == ['Japan', 'Russia'] and e['cont'] == 'Asia'
    u = geoids.names({'country': 'Atlantis'})
    assert u['country'] == 'Atlantis' and 'cont' not in u   # left as it is, so the checks can report it

def test_name_form_finds_names_and_unknowns():
    assert geoids.name_form({'country': '392', 'states': ['01']}) == []
    assert geoids.name_form({'country': 'Japan', 'countries': ['392', 'Russia'], 'states': ['Alabama']}) == ['Japan', 'Russia', 'Alabama']
    assert geoids.name_form({'country': '999'}) == ['999']   # an id that is not in geo.json is a mistake too

def test_round_trip():
    for n in ('Japan', 'Kosovo', 'Fiji'):
        assert geoids.country_name(geoids.country_id(n)) == n
    assert geoids.state_name(geoids.state_id('Alabama')) == 'Alabama' and geoids.state_id('Alabama') == '01'

if __name__ == '__main__':
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); print('ok', k)
