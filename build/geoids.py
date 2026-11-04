"""Ids for countries and states in place files (#251).

A place file may name a country or a US state by its id in data/geo/geo.json (`392`, `01`) or, until the rewrite is done, by its name.
`names(e)` returns the place with names (what the build, the app and the checks use) and the continent filled in from the country.
`ids_of(names)` is the other way, for jobs that write places. Unknown values are left as they are, so the checks can report them."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_G = {}


def tables():
    if not _G:
        geo = json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json')))
        _G['c_name'] = {c['id']: c['name'] for c in geo['countries']}
        _G['c_id'] = {c['name']: c['id'] for c in geo['countries']}
        _G['c_cont'] = {c['name']: c['cont'] for c in geo['countries']}
        _G['s_name'] = {s['id']: s['name'] for s in geo['states']}
        _G['s_id'] = {s['name']: s['id'] for s in geo['states']}
    return _G


def country_name(x): return tables()['c_name'].get(x, x)
def state_name(x): return tables()['s_name'].get(x, x)
def country_id(x): return tables()['c_id'].get(x, x)
def state_id(x): return tables()['s_id'].get(x, x)
def continent_of(country): return tables()['c_cont'].get(country_name(country))


def is_id(x, kind):
    t = tables()
    return x in t['c_name' if kind == 'country' else 's_name']


def names(e):
    """The place with country, countries and states as names and `cont` set from the country. Changes e in place and returns it."""
    if 'country' in e: e['country'] = country_name(e['country'])
    if 'countries' in e: e['countries'] = [country_name(c) for c in e['countries']]
    if 'states' in e: e['states'] = [state_name(s) for s in e['states']]
    c = continent_of(e.get('country', ''))
    if c: e['cont'] = c
    return e
