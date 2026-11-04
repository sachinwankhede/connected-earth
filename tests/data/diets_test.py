#!/usr/bin/env python3
"""build/diets.py: the global table of eating links (#256). Run: python3 tests/data/diets_test.py"""
import copy, json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import diets, species, validate_data

SP = {'grass': 'Poa pratensis', 'deer': 'Odocoileus virginianus', 'wolf': 'Canis lupus', 'sun': 'sunlight'}

def make(root):
    for k, latin in SP.items():
        sid = species.slug(latin)
        r = {'sid': sid, 'sk': 'resource' if k == 'sun' else 'taxon', 'name': latin if k == 'sun' else k, 'tl': 1}
        if k != 'sun': r['latin'] = latin
        species.write_row(r, os.path.join(root, 'data', 'species', 'rows'))
    os.makedirs(os.path.join(root, 'data', 'places'))
    def place(pid, edges, ev):
        nodes = [{'id': k, 'sp': (SP[k]).lower(), 'xh': 0.5} for k in SP if any(k in e[:2] for e in edges)]
        d = {'id': pid, 'nodes': nodes, 'raw': edges, 'ev': ev}
        open(os.path.join(root, 'data', 'places', pid + '.json'), 'w').write(json.dumps(d, ensure_ascii=False))
        return d
    same = ['g', 'Odocoileus virginianus', 'Poa pratensis']
    return {
        'a': place('a', [['sun', 'grass', 'r'], ['grass', 'deer'], ['deer', 'wolf']], {'grass>deer': same, 'deer>wolf': ['g', 'Canis lupus', 'Odocoileus virginianus']}),
        'b': place('b', [['grass', 'deer'], ['deer', 'wolf']], {'grass>deer': same, 'deer>wolf': ['gg', 'Canis lupus', 'Odocoileus']}),   # b disagrees on deer>wolf
        'c': place('c', [['grass', 'deer'], ['deer', 'wolf']], {'grass>deer': same, 'deer>wolf': ['g', 'Canis lupus', 'Odocoileus virginianus']}),
        'd': place('d', [['grass', 'deer'], ['deer', 'wolf']], {}),   # hand-made links without evidence, although the table has some for the pairs
    }

def test_pack_then_join_gives_every_place_back_unchanged():
    with tempfile.TemporaryDirectory() as root:
        orig = make(root)
        s = diets.pack(root, legacy=True)
        assert s['new_pairs'] == 2 and len(s['pairs_that_differ']) == 1, s
        tab = species.table(root); diets._cache.clear()
        for pid, o in orig.items():
            slim = json.load(open(os.path.join(root, 'data', 'places', pid + '.json')))
            full = diets.join(copy.deepcopy(slim), tab, root)
            assert full['ev'] == o['ev'] and list(full['ev']) == list(o['ev']), (pid, full['ev'], o['ev'])
        a = json.load(open(os.path.join(root, 'data', 'places', 'a.json')))
        assert a['ev'] == {}, a['ev']                                   # equal to the table: dropped
        b = json.load(open(os.path.join(root, 'data', 'places', 'b.json')))
        assert list(b['ev']) == ['deer>wolf'], b['ev']                   # differs: kept as an override
        d = json.load(open(os.path.join(root, 'data', 'places', 'd.json')))
        assert d['ev'] == {'grass>deer': None, 'deer>wolf': None}, d['ev']   # no evidence there: marked, so the join does not fill it

def test_second_pack_changes_nothing_and_never_rewrites_a_pair():
    with tempfile.TemporaryDirectory() as root:
        make(root); diets.pack(root, legacy=True)
        files = {p: open(p).read() for p in [os.path.join(dp, f) for dp, _, fs in os.walk(root) for f in fs]}
        diets._cache.clear(); s = diets.pack(root)
        assert s['new_pairs'] == 0 and s['places_changed'] == 0, s
        assert files == {p: open(p).read() for p in [os.path.join(dp, f) for dp, _, fs in os.walk(root) for f in fs]}

def test_new_place_with_known_and_new_pairs():
    with tempfile.TemporaryDirectory() as root:
        make(root); diets.pack(root, legacy=True); diets._cache.clear()
        p = os.path.join(root, 'data', 'places', 'e.json')
        d = {'id': 'e', 'nodes': [{'id': 'g', 'sp': 'poa pratensis'}, {'id': 'w', 'sp': 'canis lupus'}, {'id': 'x', 'sp': 'odocoileus virginianus'}],
             'raw': [['g', 'x'], ['x', 'w'], ['g', 'w']], 'ev': {'g>x': ['g', 'Odocoileus virginianus', 'Poa pratensis'], 'g>w': ['a']}}
        open(p, 'w').write(json.dumps(d))
        s = diets.pack(root, src='job-x')
        assert s['new_pairs'] == 1, s                                    # only grass>wolf is new
        e = json.load(open(p))
        assert e['ev'] == {}, e['ev']
        t = diets.table(root); sid = lambda k: species.slug(SP[k])
        assert t[(sid('grass'), sid('wolf'))]['src'] == 'job-x' and 'at' in t[(sid('grass'), sid('wolf'))]
        assert 'src' not in t[(sid('grass'), sid('deer'))]               # legacy entries carry no src

def test_species_pack_leaves_slimmed_places_alone():
    """species.py pack rewrites the place files; it must write back the place's own `ev`, not the joined one (found 4 Nov: it re-expanded every place)."""
    with tempfile.TemporaryDirectory() as root:
        make(root); diets.pack(root, legacy=True); diets._cache.clear()
        newp = os.path.join(root, 'data', 'places', 'e.json')   # a job adds a place with full evidence: the same pack lifts it into the table
        open(newp, 'w').write(json.dumps({'id': 'e', 'nodes': [{'id': 'g', 'sp': 'poa pratensis', 'xh': 0.1}, {'id': 'w', 'sp': 'canis lupus', 'xh': 0.9}], 'raw': [['g', 'w']], 'ev': {'g>w': ['a']}}))
        saved = (species.ROOT, species.TABLE, species.ROWS, diets.ROOT)
        species.ROOT = diets.ROOT = root; species.TABLE = os.path.join(root, 'data', 'species', 'species.json'); species.ROWS = os.path.join(root, 'data', 'species', 'rows')
        try:
            before = {p: open(p).read() for p in diets.place_files(root)}
            species.pack()
            after = {p: open(p).read() for p in diets.place_files(root)}
        finally:
            species.ROOT, species.TABLE, species.ROWS, diets.ROOT = saved
        changed = [os.path.basename(p) for p in before if before[p] != after[p]]
        for p in before:   # the nodes may be slimmed by the pack; the evidence of the existing places must be what it was
            if p == newp: continue
            assert json.loads(before[p]).get('ev') == json.loads(after[p]).get('ev'), p
        assert json.loads(after[os.path.join(root, 'data', 'places', 'a.json')])['ev'] == {}, changed
        assert json.loads(after[newp])['ev'] == {} and (species.slug(SP['grass']), species.slug(SP['wolf'])) in diets.table(root), 'the new place was not lifted'

def test_validator_checks_the_table():
    with tempfile.TemporaryDirectory() as root:
        make(root); diets.pack(root, legacy=True)
        errs, _ = validate_data.check(root)
        assert not [e for e in errs if 'diets' in e], errs
        sid = species.slug(SP['wolf']); p = os.path.join(root, 'data', 'diets', sid[:2], sid + '.json')
        o = json.load(open(p)); o['prey']['no-such-species'] = {'ev': ['a'], 'k': 'e'}; o['prey'][species.slug(SP['deer'])]['k'] = 'x'
        json.dump(o, open(p, 'w'))
        errs, _ = validate_data.check(root)
        text = '\n'.join(errs)
        assert 'no-such-species' in text and "'x'" in text, text

if __name__ == '__main__':
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); print('ok', k)
