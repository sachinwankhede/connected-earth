#!/usr/bin/env python3
"""The places cut by region (item #313, step 2): together the files hold exactly the places of the split (index and cards), each place once, and the counts are right."""
import json, os, sys, itertools
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def check(pilot, folder):
    links, ecos = B.load_places(pilot)
    errs = B.check(ecos, links, B.app_source(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))
    assert not errs, errs[:3]
    light = B.split(ecos, links)[0]
    index, cards = B.split_places(light)
    files = B.split_regions(light)
    by = {e['id']: e for e in index}
    # every place is in exactly one of the world file and the region shards, with the same content as the split
    seen = {}
    parts = [('world', files['index-world.json'], files['cards-world.json'])] + [(f[6:-5], files[f], files['cards-' + f[6:]]) for f in sorted(files) if f.startswith('index-') and f not in ('index-world.json', 'index-local.json')]
    for name, rows, cs in parts:
        assert [e['id'] for e in rows] and set(cs) == {e['id'] for e in rows}, name + ': index and cards list the same places'
        for e in rows:
            assert e['id'] not in seen, e['id'] + ' is in two files'
            seen[e['id']] = name
            assert e == by[e['id']] and cs[e['id']] == cards[e['id']], e['id'] + ' differs from the split'
    assert set(seen) == set(by), 'every place is in a file'
    assert all((by[i].get('level') == 'local') == (n != 'world') for i, n in seen.items()), 'world holds the places that are not local, shards the local ones'
    # index-local / cards-local: all the local places together, in page order, each as in the split
    want = [e for e in index if e.get('level') == 'local']
    assert files['index-local.json'] == want and files['cards-local.json'] == {e['id']: cards[e['id']] for e in want}, 'the local files hold every local place'
    # a local place is in the shard of its state (or its continent outside the US states)
    for i, n in seen.items():
        if n != 'world': assert n == B.region_key(by[i]), i
    # the page order is kept inside each file
    order = {e['id']: k for k, e in enumerate(index)}
    for name, rows, _ in parts: assert [order[e['id']] for e in rows] == sorted(order[e['id']] for e in rows), name + ' keeps page order'
    # positions
    kinds = files['positions.json']['kinds']
    for fn, want in (('positions.json', [e for e in index if e.get('level') != 'local']), ('positions-local.json', [e for e in index if e.get('level') == 'local'])):
        got = files[fn]['p']
        assert [r[0] for r in got] == [e['id'] for e in want], fn
        for r, e in zip(got, want):
            assert r[1] == e['short'] and r[2] == e['lat'] and r[3] == e['lon'] and kinds[r[4]] == e['kind'] and r[5] == (1 if e.get('auto') else 0) + (2 if e.get('park') else 0), e['id']
            g = files[fn]['g'][r[6]]   # membership and shard key
            assert g == [e['conts'], e['countries'], e.get('states') or []] and r[7] == (B.region_key(e) if e.get('level') == 'local' else 'world'), e['id']
    # counts: every region, brute force
    regions = files['counts.json']['regions']
    def members(name):
        if name == 'w': return index
        t, v = name.split(':', 1)
        f = {'c': 'conts', 'k': 'countries', 's': 'states'}[t]
        return [e for e in index if v in (e.get(f) or [])]
    names = {'w'} | {'c:' + c for e in index for c in e['conts']} | {'k:' + c for e in index for c in e['countries']} | {'s:' + c for e in index for c in e.get('states') or []}
    assert set(regions) == names, 'one entry per region'
    for name, r in regions.items():
        m = members(name)
        for l in (0, 1):
            ml = [e for e in m if (e.get('level') == 'local') == bool(l)]
            assert r['n'][l] == len(ml), name
            assert r['p'][l] == sum(1 for e in ml if e.get('park')), name
            for k in kinds: assert r['k'].get(k, [0, 0])[l] == sum(1 for e in ml if e['kind'] == k), (name, k)
        assert r['s'] == sorted({B.region_key(e) for e in m if e.get('level') == 'local'}), name + ': shards of the region'
    # the built folder (when the build has run) is exactly this
    d = os.path.join(ROOT, 'api', 'places', folder)
    if os.path.isdir(d):
        assert set(os.listdir(d)) == set(files), 'stale or missing files in api/places/' + folder
        for f, obj in files.items(): assert json.load(open(os.path.join(d, f))) == obj, f
    return len(index), len(files), len(regions)

n, f, r = check(False, 'main'); m, _, _ = check(True, 'pilot')
assert n > 1000 and m > n
print('places by region ok: main %d places in %d files, %d regions; pilot %d places' % (n, f, r, m))
