#!/usr/bin/env python3
"""Related places, ties and species-to-places (items #252, #253): the build's answers equal what the app used to work out by scanning every place's species list.
The scans below are written the way the old browser code did them (nested loops over the list of places), apart from the build's own code."""
import json, os, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

def old_scan(ecos):
    sp = {e['id']: [[n['latin'], n['name']] for n in e['nodes'] if not n.get('cat') and n.get('latin')] for e in ecos}
    rel, ties, where = {}, {}, {}
    for e in ecos:   # "Shares species with": places other than this one, species in common, most first (stable), at most 10
        mine = {l for l, _ in sp[e['id']]}
        near = [(o['id'], sum(1 for m in sp[o['id']] if m[0] in mine)) for o in ecos if o['id'] != e['id']]
        rel[e['id']] = [[i, c] for i, c in sorted([x for x in near if x[1] > 0], key=lambda x: -x[1])[:10]]
    by = collections.OrderedDict()   # ties: species found in 2 to 10 places
    for e in ecos:
        for l, name in sp[e['id']]: by.setdefault(l, []).append((e['id'], name))
    t = {}
    for l, g in by.items():
        if len(g) < 2 or len(g) > 10: continue
        for a, an in g:
            for b, _ in g:
                if a != b: t.setdefault(a, {}).setdefault(b, []).append(an)
    for a, d in t.items(): ties[a] = [[b, d[b]] for b in sorted(d, key=lambda b: (-len(d[b]), b))]
    for l in by:   # "Also found in": every place that lists the species
        hits = []
        for e in ecos:
            if any(m[0] == l for m in sp[e['id']]) and e['id'] not in hits: hits.append(e['id'])
        if len(hits) >= 2: where[l] = hits
    return rel, ties, where


def check(pilot):
    links, ecos = B.load_places(pilot)
    rel, ties, where = B.species_overlap(ecos)
    orel, oties, owhere = old_scan(ecos)
    assert rel == orel, 'related places differ from the old scan: ' + next(i for i in orel if rel[i] != orel[i])
    assert ties == oties, 'ties differ from the old scan'
    assert where == owhere, 'species to places differs from the old scan'
    assert all(len(v) <= B.RELATED_N for v in rel.values())
    # the files: every species is in the file of its bucket, and the buckets hold exactly the lists
    files = B.split_species_places(where)
    assert {k: v for f in files.values() for k, v in f.items()} == where and all(B.species_bucket(l) + '.json' == f for f, d in files.items() for l in d)
    assert all(len(f) == 7 and f.endswith('.json') for f in files), 'a bucket is two characters'
    # the ties files: per region, the first 16 of the old scan's list, the first 5 with count and up to 3 names, the rest as bare ids
    errs = B.check(ecos, links, open(os.path.join(ROOT, 'src', 'app.html')).read(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))   # fills in the derived fields (countries) the region key needs
    assert not errs, errs[:3]
    light = B.split(ecos, links)[0]
    files = B.split_ties(light, oties)
    seen = {}
    for f, d in files.items():
        for i, rows in d.items():
            assert i not in seen, i + ' is in two ties files'
            seen[i] = f
            want = oties[i][:16]
            assert [r[0] if isinstance(r, list) else r for r in rows] == [b for b, _ in want], i + ': ties order'
            for r, (b, names) in zip(rows, want):
                if isinstance(r, list): assert r == [b, len(names), names[:3]], i + ': ties names'
            assert all(isinstance(r, list) for r in rows[:5]) and all(isinstance(r, str) for r in rows[5:]), i + ': named entries come first'
    assert set(seen) == set(oties), 'every place with ties is in a file'
    light_by = {e['id']: e for e in light}
    assert all(f == ('world.json' if light_by[i].get('level') != 'local' else B.region_key(light_by[i]) + '.json') for i, f in seen.items()), 'a ties file is the place region file'
    return rel, ties, where, files

mrel, mties, mwhere, mfiles = check(False)
prel, pties, pwhere, pfiles = check(True)
assert len(prel) > len(mrel) and mwhere != pwhere, 'main and pilot are different sets'

# the answers inside the place files (the pilot build writes them for both pages)
links, ecos = B.load_places(True)
main_ids = set(links['order'])
webs = {e['id']: {} for e in ecos}
B.add_overlap(webs, ecos, main_ids)
for e in ecos:
    i, w = e['id'], webs[e['id']]
    if i in main_ids:
        assert w.get('rel', []) == mrel[i], i + ': the main answer is wrong'
        assert w.get('relp', w.get('rel', [])) == prel[i], i + ': the pilot answer is wrong'
    else:
        assert 'rel' not in w, i + ': a pilot-only place has a main answer'
        assert w.get('relp', []) == prel[i], i + ': the pilot answer is wrong'

# the built files (when the build has run) are exactly this
for folder, where in (('species-places', mwhere), ('species-places-pilot', pwhere)):
    pass
for folder, want in (('ties', mfiles), ('ties-pilot', pfiles)):
    d = os.path.join(ROOT, 'api', folder)
    if os.path.isdir(d):
        assert set(os.listdir(d)) == set(want), 'stale or missing files in api/' + folder
        assert all(json.load(open(os.path.join(d, f))) == want[f] for f in want), 'api/' + folder + ' differs from the build'
for folder, where in (('species-places', mwhere), ('species-places-pilot', pwhere)):
    d = os.path.join(ROOT, 'api', folder)
    if os.path.isdir(d):
        want = B.split_species_places(where)
        assert set(os.listdir(d)) == set(want), 'stale or missing files in api/' + folder
        assert all(json.load(open(os.path.join(d, f))) == want[f] for f in want), 'api/' + folder + ' differs from the build'
    w = os.path.join(ROOT, 'api', 'gulf.json')
if os.path.exists(os.path.join(ROOT, 'api', 'gulf.json')):
    for e in ecos:
        f = json.load(open(os.path.join(ROOT, 'api', e['id'] + '.json')))
        assert not ({'ties', 'tiesp'} & set(f)) and {k: f[k] for k in ('rel', 'relp') if k in f} == webs[e['id']], e['id'] + ': the place file differs from the build'
print('ok')
