#!/usr/bin/env python3
"""#934, #974: a place file lists a species' picture under its species id (the slug of its Latin name), not under a title two species can share.
A species with a picture of its own is listed by id only; a species without one is listed under nothing: it no longer borrows the picture of a title (#973 phase 4)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def row(f, page, **kw): return {'f': f, 'page': page, 'wiki': kw.get('wiki', page), 'a': 'An Author', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg'}
nodes = [
    {'id': 'a', 'sid': 'canis-lupus', 'name': 'Wolf', 'latin': 'Canis lupus', 'wiki': 'Gray wolf', 'tl': 3},                  # own picture
    {'id': 'b', 'sid': 'canis-rufus', 'name': 'Red wolf', 'latin': 'Canis rufus', 'wiki': 'Gray wolf', 'tl': 3},              # shares the title of a, has no picture of its own
    {'id': 'c', 'sid': 'bryum-argenteum', 'name': 'Moss', 'latin': 'Bryum argenteum', 'wiki': 'Bryum', 'tl': 1},                  # no own picture, title entry exists
    {'id': 'd', 'name': 'Rain', 'cat': 'rain', 'wiki': 'Rain', 'tl': 0},                                 # not a species
]
ecos = [{'id': 'testplace', 'nodes': nodes, 'raw': []}]
sp = {'pics': {'canis-lupus': row('aaaaaaaaaaaa.webp', 'Canis_lupus', wiki='Gray wolf')}}
webs = B.split(ecos, {'cross': [], 'order': [], 'src': {}, 'couple': 0}, sp)[1]['testplace']
ph, pm = webs['ph'], webs['phm']
assert ph['canis-lupus'] == ['aaaaaaaaaaaa.webp', 'Canis_lupus'], ph                     # listed under its species id
assert 'canis-lupus' in pm and pm['canis-lupus']['a'] == 'An Author', pm                 # with its credit, by id
assert set(ph) == {'canis-lupus'} and set(pm) == {'canis-lupus'}, (ph, pm)           # no title entry: the red wolf (same title as the gray wolf) and the moss (a title picture exists) show none
print('ok')
