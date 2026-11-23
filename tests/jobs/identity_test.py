#!/usr/bin/env python3
"""jobs/identity.py: rows map to the item of their page, with rank and taxon name; missing pages and rows without a page say why."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import identity as ID
def get(url):
    if 'prop=pageprops' in url:
        return {'query': {'pages': {'1': {'title': 'Zooplankton', 'pageprops': {'wikibase_item': 'Q1'}}, '2': {'title': 'Ficus', 'pageprops': {'wikibase_item': 'Q2'}}, '3': {'title': 'Nowhere', 'missing': ''}}}}
    return {'entities': {'Q1': {'claims': {}}, 'Q2': {'claims': {'P105': [{'mainsnak': {'datavalue': {'value': {'id': 'Q34740'}}}}], 'P225': [{'mainsnak': {'datavalue': {'value': 'Ficus'}}}]}}}}
rows = [{'sid': 'a', 'wiki': 'Zooplankton', 'sk': 'group'}, {'sid': 'b', 'wiki': 'Ficus', 'sk': 'group'}, {'sid': 'c', 'wiki': 'Nowhere', 'sk': 'resource'}, {'sid': 'd', 'sk': 'taxon'}]
r = ID.decide(rows, get)
assert r['a'][:3] == ['Q1', '', ''] and r['b'][:3] == ['Q2', 'Q34740', 'Ficus'], r
assert r['c'][0] == '' and 'missing' in r['c'][4] and r['d'][4] == 'row has no page', r
print('identity ok')
