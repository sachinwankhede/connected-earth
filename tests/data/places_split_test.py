#!/usr/bin/env python3
"""The two places files (item #228, step 1): index + cards must hold exactly the light place of the page, with no field in both."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def check(pilot, sfx):
    links, ecos = B.load_places(pilot)
    # the build's check() fills in derived fields (countries) on the places before they are split: do the same
    errs = B.check(ecos, links, open(os.path.join(ROOT, 'src', 'app.html')).read(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))
    assert not errs, errs[:3]
    light = B.split(ecos, links)[0]
    index, cards = B.split_places(light)
    assert len(index) == len(light) == len(cards), 'one entry per place'
    assert [i['id'] for i in index] == [e['id'] for e in light], 'index keeps the page order'
    for i, e in zip(index, light):
        c = cards[e['id']]
        assert 'id' not in c, e['id'] + ': id is only in the index'
        assert not (set(i) & set(c)) - {'id'}, e['id'] + ': a field is in both files'
        assert {**i, **c} == e, e['id'] + ': index + cards is not the light place'
    # the built files (when the build has run) are exactly this split
    d = os.path.join(ROOT, 'api', 'places')
    for name, want in (('index', index), ('cards', cards)):
        p = os.path.join(d, name + sfx + '.json')
        if os.path.exists(p): assert json.load(open(p)) == want, p + ' differs from the split'
    return len(light)

n = check(False, ''); m = check(True, '-pilot')
assert n > 1000 and m > n, 'main and pilot sets'
extra = set(os.listdir(os.path.join(ROOT, 'api', 'places'))) - set(B.PLACES_FILES) if os.path.isdir(os.path.join(ROOT, 'api', 'places')) else set()
assert not extra, 'stale files in api/places: %s' % sorted(extra)
assert set(B.INDEX_FIELDS) >= {'id', 'lat', 'lon', 'kind', 'short'}
print('places split ok: main %d, pilot %d' % (n, m))
