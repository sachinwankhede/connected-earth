#!/usr/bin/env python3
"""#934, #974: a place file lists a species' picture under its species id (the slug of its Latin name), not under a title two species can share.
A species with a picture of its own is listed by id only; a species without one keeps the title entries it had (the picture of a title one of its nodes carries)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def row(f, page, **kw): return {'f': f, 'page': page, 'wiki': kw.get('wiki', page), 'a': 'An Author', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg'}
nodes = [
    {'id': 'a', 'name': 'Wolf', 'latin': 'Canis lupus', 'wiki': 'Gray wolf', 'tl': 3},                  # own picture
    {'id': 'b', 'name': 'Red wolf', 'latin': 'Canis rufus', 'wiki': 'Gray wolf', 'tl': 3},              # shares the title of a, has no picture of its own
    {'id': 'c', 'name': 'Moss', 'latin': 'Bryum argenteum', 'wiki': 'Bryum', 'tl': 1},                  # no own picture, title entry exists
    {'id': 'd', 'name': 'Rain', 'cat': 'rain', 'wiki': 'Rain', 'tl': 0},                                 # not a species
]
ecos = [{'id': 'testplace', 'nodes': nodes, 'raw': []}]
sp = {'pics': {'canis-lupus': row('aaaaaaaaaaaa.webp', 'Canis_lupus', wiki='Gray wolf')}}
phs = {'Gray wolf': ['aaaaaaaaaaaa.webp', 'Canis_lupus'], 'Bryum': ['bbbbbbbbbbbb.webp', 'Bryum']}
phm = {'Gray wolf': {'a': 'An Author', 'l': 'CC BY 4.0'}, 'Bryum': {'a': 'Other', 'l': 'CC0'}}
webs = B.split(ecos, {'cross': [], 'order': [], 'src': {}, 'couple': 0}, phs, phm, sp)[1]['testplace']
ph, pm = webs['ph'], webs['phm']
assert ph['canis-lupus'] == ['aaaaaaaaaaaa.webp', 'Canis_lupus'], ph                     # listed under its species id
assert 'canis-lupus' in pm and pm['canis-lupus']['a'] == 'An Author', pm                 # with its credit, by id
assert 'Gray wolf' in ph, 'the species without a picture of its own keeps the title entry (the borrow stays until the last phase)'
assert ph['Bryum'] == ['bbbbbbbbbbbb.webp', 'Bryum'], ph                                  # unchanged for a species without its own picture
# with no species pictures by id (the old shape alone) the lists are as they were: titles only
old = B.split(ecos, {'cross': [], 'order': [], 'src': {}, 'couple': 0}, phs, phm)[1]['testplace']
assert set(old['ph']) == {'Gray wolf', 'Bryum'} and 'canis-lupus' not in old['ph'], old['ph']
print('ok')
