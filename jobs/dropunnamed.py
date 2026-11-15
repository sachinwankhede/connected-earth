#!/usr/bin/env python3
"""dropunnamed.py: remove CC BY and CC BY-SA pictures that cannot be credited (#887; owner, 15 Nov: "remove the pictures which don't have license information and author").
Usage: dropunnamed.py [--dry]   (run from the repository root; --dry prints the list and changes nothing)
Takes the pictures jobs/authorlookup.py picks (CC BY or CC BY-SA, stored author unknown), asks Commons again for each, and removes those for which no author can be found (class `none`).
A picture whose author Commons now gives (artist, attribution, own work) is kept: filling in names is a separate decision.
Removal goes through jobs/droppictures.py: places (with their larger copy; the place goes to missing.json as 'notfree'), species (every row; Commons is not asked again for 90 days). Host: commons.wikimedia.org."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import authorlookup as al, droppictures as dp

def split(rows):
    """(place keys, species keys) of the rows whose class is 'none'."""
    return sorted(r['key'] for r in rows if r['kind'] == 'place' and r['class'] == 'none'), sorted(r['key'] for r in rows if r['kind'] == 'species' and r['class'] == 'none')

def main():
    load = lambda p: json.load(open(os.path.join(ROOT, p))) if os.path.exists(os.path.join(ROOT, p)) else {}
    cands = al.candidates(load('photos/places/places.json'), load('photos/species_metadata.json')); print(len(cands), 'candidates', flush=True)
    rows = []
    for k, c in enumerate(cands, 1):
        c['class'], c['name'] = al.lookup(c['file']); rows.append(c)
        if k % 10 == 0: print(k, 'of', len(cands), flush=True)
    places, species = split(rows); dry = '--dry' in sys.argv
    bp, _ = dp.drop_places(ROOT, dry, titles=places) if places else ([], None)
    bs, _ = dp.drop(ROOT, dry, titles=species, hold=True) if species else ([], None)
    print(len(bp), 'place pictures', 'to remove' if dry else 'removed', '|', len(bs), 'species pictures', 'to remove' if dry else 'removed')
    for t in bp: print('place', t)
    for t in bs: print('species', t)
    print('kept (an author was found):', sum(1 for r in rows if r['class'] != 'none'))
if __name__ == '__main__': main()
