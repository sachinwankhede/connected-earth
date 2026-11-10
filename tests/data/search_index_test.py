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
    errs = B.check(ecos, links, B.app_source(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))
    assert not errs, errs[:3]
    light, webs, spt, sidx, qs = B.split(ecos, links)
    meta, buckets, rows = B.split_search(light, spt, sidx, qs)
    words = decode(buckets)
    assert meta['n'] == len(light) and meta['buckets'] == sorted(buckets)
    # every word of every place finds that place; nothing else does
    want = {}
    for n, e in enumerate(light):
        names = []; alias = set()
        for k in sidx[e['id']]:
            lat, common = (spt[k][0], spt[k][1]) if isinstance(k, int) else (spt[k[0]][0], k[1])
            names += [common, lat]; alias |= B.search_aliases(common)   # other words for the same name (#602)
        for w in B.search_words(' '.join([e['name'], e['place'], e['short'], e.get('kind') or '', qs[e['id']]] + names)) | alias: want.setdefault(w, []).append(n)
    assert words == want, 'index differs from the places'
    # rows: one line per place in page order
    flat = [r for f in rows for r in f]
    assert len(flat) == len(light) and all(len(f) == meta['rows'] for f in rows[:-1])
    for e, r in zip(light, flat): assert r[0] == e['id'] and r[1] == e['name'] and r[2] == e['place'] and r[5] == e['cont'], e['id']
    # a name the user would type
    assert 'yellowstone' in words and light[words['yellowstone'][0]]['id'] == 'yellowstone'
    assert B.search_words("Cooper's Hawk, São Tomé") >= {'coopers', 'hawk', 'sao', 'tome'}
    # other words for the same name (#602): plurals, irregular plurals both ways, spelling pairs; never the word itself
    assert B.search_aliases('Elk') == {'elks'} and B.search_aliases('Gray wolf') == {'grey', 'wolves'} and B.search_aliases('Grey wolves') == {'gray', 'wolf'}
    assert B.search_aliases('Osprey') == {'ospreys'} and B.search_aliases('Brown bush mouse') == {'mice'} and B.search_aliases('Red fox') == {'foxes'} and B.search_aliases('Lady fern') == {'ferns'}
    assert B.search_aliases('Sea cherry') == {'cherries'} and B.search_aliases('Mule deer') == set() and B.search_aliases('') == set()
    assert 'wolves' in words and 'grey' in words, 'the index has the forms'
    # the built folder (when the build has run) is exactly this
    d = os.path.join(ROOT, 'api', folder)
    if os.path.isdir(d):
        sug = B.split_suggest(light, spt, sidx)
        files = {'meta.json': meta} | {'w-%s.json' % k: v for k, v in buckets.items()} | {'rows-%d.json' % i: r for i, r in enumerate(rows)} | {'s-%s.json' % k: v for k, v in sug.items()}   # s-: suggestions (#413)
        files['meta.json'] = meta | {'sug': sorted(sug)}   # the build adds the list of suggestion files to meta
        assert set(os.listdir(d)) == set(files), 'stale or missing files in api/' + folder
        def bare(obj, f):   # a species row also carries its hosted picture file (#443); it is checked in search_suggest_test
            return {'p': obj['p'], 's': [r[:3] for r in obj['s']]} if f.startswith('s-') else obj
        for f, obj in files.items(): assert bare(json.load(open(os.path.join(d, f))), f) == bare(obj, f), f
    return len(light), len(words)

n, w = check(False, 'search'); m, _ = check(True, 'search-pilot')
assert n > 1000 and m > n
print('search index ok: main %d places, %d words; pilot %d places' % (n, w, m))
