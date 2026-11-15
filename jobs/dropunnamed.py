#!/usr/bin/env python3
"""dropunnamed.py: remove CC BY and CC BY-SA pictures that cannot be credited (#887; owner, 15 Nov: "remove the pictures which don't have license information and author").
Usage: dropunnamed.py [--dry]   (run from the repository root; --dry prints the list and changes nothing)
Takes the pictures jobs/authorlookup.py picks (CC BY or CC BY-SA, stored author unknown), asks Commons again for each, and removes those for which no author can be found (class `none`).
A picture whose author Commons now gives (artist, attribution, own work) is kept and its stored author is filled in with that name (owner, 15 Nov: "update the missing name at the same time").
Removal goes through jobs/droppictures.py: places (with their larger copy; the place goes to missing.json as 'notfree'), species (by sid once photos/species_pictures.json exists, by title before; Commons is not asked again for 90 days). Host: commons.wikimedia.org."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from place_photos import PlacePhotos
from species_photos import SpeciesPhotos
import species_pics
import authorlookup as al, droppictures as dp

def split(rows):
    """(place keys, species keys) of the rows whose class is 'none'."""
    return sorted(r['key'] for r in rows if r['kind'] == 'place' and r['class'] == 'none'), sorted(r['key'] for r in rows if r['kind'] == 'species' and r['class'] == 'none')

def fills(rows):
    """{'place': {key: name}, 'species': {key: name}} for the rows where Commons gave a name."""
    out = {'place': {}, 'species': {}}
    for r in rows:
        if r['class'] != 'none' and r['name']: out[r['kind']][r['key']] = r['name']
    return out

def fill(root, names, dry=False):
    """Write the found names into the stored author ('a') of places.json and species_metadata.json; only rows whose author is still unknown. Returns how many were filled."""
    n = 0
    if names['place']:
        w = PlacePhotos(root); changed = 0
        for k, name in names['place'].items():
            if k in w.pics and al.unknown(w.pics[k].get('a')): w.pics[k]['a'] = name; changed += 1
        n += changed
        if changed and not dry: w.commit()   # places go through the one writer (#887)
    if names['species'] and species_pics.new_shape(root):   # keyed by sid, through the one writer (#934)
        w = SpeciesPhotos(root); changed = 0
        for k, name in names['species'].items():
            if k in w.pics and al.unknown(w.pics[k].get('a')): w.pics[k]['a'] = name; changed += 1
        n += changed
        if changed and not dry: w.commit()
        return n
    p = os.path.join(root, 'photos/species_metadata.json')
    if names['species'] and os.path.exists(p):
        d = json.load(open(p, encoding='utf-8')); changed = 0
        for k, name in names['species'].items():
            if k in d and al.unknown(d[k].get('a')): d[k]['a'] = name; changed += 1
        n += changed
        if changed and not dry: json.dump(d, open(p, 'w', encoding='utf-8'), indent=0, sort_keys=True, ensure_ascii=False)   # the layout droppictures.py keeps
    return n

def main():
    load = lambda p: json.load(open(os.path.join(ROOT, p))) if os.path.exists(os.path.join(ROOT, p)) else {}
    cands = al.candidates(load('photos/places/places.json'), al.species_credits(ROOT)); print(len(cands), 'candidates', flush=True)
    rows = []
    for k, c in enumerate(cands, 1):
        c['class'], c['name'] = al.lookup(c['file']); rows.append(c)
        if k % 10 == 0: print(k, 'of', len(cands), flush=True)
    places, species = split(rows); dry = '--dry' in sys.argv
    bp, _ = dp.drop_places(ROOT, dry, titles=places) if places else ([], None)
    bs, _ = dp.drop(ROOT, dry, titles=species, hold=True) if species else ([], None)
    names = fills(rows); nf = fill(ROOT, {k: {t: v for t, v in m.items() if t not in set(bp) | set(bs)} for k, m in names.items()}, dry)
    print(nf, 'stored authors', 'to fill in' if dry else 'filled in')
    for kind in ('place', 'species'):
        for t, v in sorted(names[kind].items()): print('name', kind, t, '=', v)
    print(len(bp), 'place pictures', 'to remove' if dry else 'removed', '|', len(bs), 'species pictures', 'to remove' if dry else 'removed')
    for t in bp: print('place', t)
    for t in bs: print('species', t)
    print('kept (an author was found):', sum(1 for r in rows if r['class'] != 'none'))
if __name__ == '__main__': main()
