#!/usr/bin/env python3
"""The suggestion files (item #413): api/search/s-<two letters>.json. Every entry belongs under the start of one of its words, the counts are right, the order is
the home list order (places) and most places first (species), and a start with fewer entries than the cap is complete."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def check(pilot):
    links, ecos = B.load_places(pilot)
    light, webs, spt, sidx, qs = B.split(ecos, links)
    sug = B.split_suggest(light, spt, sidx)
    byid = {e['id']: (n, e) for n, e in enumerate(light)}
    latin_places = {}
    for e in light:
        for k in sidx[e['id']]: latin_places.setdefault(spt[k if isinstance(k, int) else k[0]][0], set()).add(e['id'])
    common = dict((l, c) for l, c in spt)
    full_p, full_s = {}, {}
    for e in light:
        for w in B.search_words(e['name'] + ' ' + e['short']): full_p.setdefault(B.search_bucket(w), set()).add(e['id'])
    for l, c in spt:
        if l in latin_places:
            for w in B.search_words(c + ' ' + l) | B.search_aliases(c): full_s.setdefault(B.search_bucket(w), set()).add(l)
    assert set(sug) == set(full_p) | set(full_s), 'one file for every start that has a name'
    for key, b in sug.items():
        assert all(len(r) in (4, 5) and (r[3] == 0 or r[3].endswith('.webp')) and (len(r) == 4 or (isinstance(r[4], str) and r[4])) for r in b['s']), key + ': a species row is [latin, name, places, hosted picture or 0] and, when there are other words for the name, a fifth field with them (#443, #602)'
        assert len(b['p']) <= B.SUGGEST_PER and len(b['s']) <= B.SUGGEST_PER
        ns = [byid[i][0] for i, _ in b['p']]
        assert ns == sorted(ns) and len(set(ns)) == len(ns), key + ': places in page order, once each'
        for i, name in b['p']:
            assert name == byid[i][1]['name'] and i in full_p[key], key + ': ' + i
        cs = [(-r[2], r[1]) for r in b['s']]
        assert cs == sorted(cs), key + ': species most places first'
        for l, c, n, _pic, *_alias in b['s']:
            assert c == common[l] and n == len(latin_places[l]) and l in full_s[key], key + ': ' + l
        if len(b['p']) < B.SUGGEST_PER: assert {i for i, _ in b['p']} == full_p.get(key, set()), key + ': places complete'
        if len(b['s']) < B.SUGGEST_PER: assert {r[0] for r in b['s']} == full_s.get(key, set()), key + ': species complete'
    return len(sug)

if __name__ == '__main__':
    for pilot in (False, True): print('pilot' if pilot else 'main', check(pilot), 'starts ok')
