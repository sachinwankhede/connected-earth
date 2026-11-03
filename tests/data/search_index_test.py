#!/usr/bin/env python3
"""The search index files (item #260, step 1): every word of a place leads to that place, no word leads anywhere else, and the rows give each place's result line."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def decode(buckets):
    """{word: [place numbers]} from the delta-coded bucket files."""
    out = {}
    for key, b in buckets.items():
        assert b['w'] == sorted(b['w']), key + ': words are sorted'
        for w, ds in zip(b['w'], b['p']):
            assert w[:2] == key, w + ' is in the wrong bucket'
            ns, t = [], 0
            for d in ds: t += d; ns.append(t)
            assert ns == sorted(set(ns)) and ds[0] >= 0 and all(d > 0 for d in ds[1:]), w + ': place numbers ascend'
            out[w] = ns
    return out

def check(pilot, folder):
    links, ecos = B.load_places(pilot)
    errs = B.check(ecos, links, open(os.path.join(ROOT, 'src', 'app.html')).read(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))
    assert not errs, errs[:3]
    light, webs, spt, sidx, qs = B.split(ecos, links)
    meta, buckets, rows = B.split_search(light, spt, sidx, qs)
    words = decode(buckets)
    assert meta['n'] == len(light) and meta['buckets'] == sorted(buckets)
    # every word of every place finds that place; nothing else does
    want = {}
    for n, e in enumerate(light):
        names = []
        for k in sidx[e['id']]:
            lat, common = (spt[k][0], spt[k][1]) if isinstance(k, int) else (spt[k[0]][0], k[1])
            names += [common, lat]
        for w in B.search_words(' '.join([e['name'], e['place'], e['short'], e.get('kind') or '', qs[e['id']]] + names)): want.setdefault(w, []).append(n)
    assert words == want, 'index differs from the places'
    # rows: one line per place in page order
    flat = [r for f in rows for r in f]
    assert len(flat) == len(light) and all(len(f) == meta['rows'] for f in rows[:-1])
    for e, r in zip(light, flat): assert r[0] == e['id'] and r[1] == e['name'] and r[2] == e['place'] and r[5] == e['cont'], e['id']
    # a name the user would type
    assert 'yellowstone' in words and light[words['yellowstone'][0]]['id'] == 'yellowstone'
    assert B.search_words("Cooper's Hawk, São Tomé") >= {'coopers', 'hawk', 'sao', 'tome'}
    # the built folder (when the build has run) is exactly this
    d = os.path.join(ROOT, 'api', folder)
    if os.path.isdir(d):
        files = {'meta.json': meta} | {'w-%s.json' % k: v for k, v in buckets.items()} | {'rows-%d.json' % i: r for i, r in enumerate(rows)}
        assert set(os.listdir(d)) == set(files), 'stale or missing files in api/' + folder
        for f, obj in files.items(): assert json.load(open(os.path.join(d, f))) == obj, f
    return len(light), len(words)

n, w = check(False, 'search'); m, _ = check(True, 'search-pilot')
assert n > 1000 and m > n
print('search index ok: main %d places, %d words; pilot %d places' % (n, w, m))
