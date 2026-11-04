#!/usr/bin/env python3
"""The global table of eating links (#256). The evidence for "A is eaten by B" (GloBI level, source name) is a fact about two species, not about a place, so it is
stored once: data/diets/<first two letters of sid>/<sid of the consumer>.json = {"sid": ..., "prey": {<sid of the prey>: {"ev": [...], "k": "e"|"s", "src": ..., "at": ...}}}.
An entry without `src` is legacy (written by the one-off that built the table). Only eating links (kind e or s) are in the table; sunlight, rain, soil and decomposer edges have no evidence.
A place file keeps `raw` (which of its own nodes are linked: the per-place presence) and an `ev` entry only where it differs from the table (an override), where the table has none, or `null` where
the place has the link without evidence although the table has some for the pair (a hand-made link; the one-off `--legacy` run writes these, later runs do not: a link without an entry takes the table's evidence).
  (python3 build/species.py pack runs this too, so the data jobs and the CI check need nothing extra)
  python3 build/diets.py pack [--legacy] [--check]   lift evidence of the place files into the table and drop what equals it (safe to repeat; never rewrites a pair that is in the table)
join() gives a place its full `ev` back; species.join calls it, so the build, the validator and the jobs see full places."""
import collections, datetime, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EATS = ('e', 's')
_cache = {}


def dir_of(root=None): return os.path.join(root or ROOT, 'data', 'diets')
def path_of(sid, root=None): return os.path.join(dir_of(root), sid[:2], sid + '.json')
def kind_of(r): return r[2] if len(r) > 2 else 'e'


def table(root=None):
    """{(prey sid, consumer sid): entry}. Empty when data/diets/ does not exist."""
    d = dir_of(root)
    if d in _cache: return _cache[d]
    out = {}
    if os.path.isdir(d):
        for sub in sorted(os.listdir(d)):
            for f in sorted(os.listdir(os.path.join(d, sub))):
                if f.endswith('.json'):
                    o = json.load(open(os.path.join(d, sub, f)))
                    for prey, e in o['prey'].items(): out[(prey, o['sid'])] = e
    _cache[d] = out
    return out


def join(eco, tab, root=None):
    """Give the place its full `ev`: its own entries (overrides) plus the table's evidence for every eating link it has none for. In raw order, as the files were written."""
    t = table(root)
    if not t or not eco.get('raw'): return eco
    sid = {n['id']: (tab.get(n.get('sp')) or {}).get('sid') for n in eco['nodes']}
    own = eco.get('ev') or {}; out = {}
    for r in eco['raw']:
        k = r[0] + '>' + r[1]
        if k in out: continue
        if k in own:
            if own[k] is not None: out[k] = own[k]   # null: this place says the link has no evidence, although the table has some for the pair
        elif kind_of(r) in EATS:
            e = t.get((sid.get(r[0]), sid.get(r[1])))
            if e and 'ev' in e: out[k] = list(e['ev'])
    for k, v in own.items():
        if v is not None: out.setdefault(k, v)
    if out or 'ev' in eco: eco['ev'] = out
    return eco


def place_files(root):
    d = os.path.join(root, 'data', 'places')
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.json') and f not in ('links.json', 'order.json', 'species.json', 'bounds.json')]


def pack(root=None, legacy=False, check=False, src=None):
    """Returns a summary dict. Without `check`, writes the new table entries and the slimmed place files."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import species
    root = root or ROOT; tab = species.table(root); t = dict(table(root))
    places = {}; occ = collections.defaultdict(list)
    for p in place_files(root):
        d = json.load(open(p)); places[p] = d; nm = {n['id']: n.get('sp') for n in d['nodes']}
        for r in d['raw']:
            if kind_of(r) not in EATS: continue
            k = r[0] + '>' + r[1]; ev = (d.get('ev') or {}).get(k)
            a, b = (tab.get(nm.get(r[0])) or {}).get('sid'), (tab.get(nm.get(r[1])) or {}).get('sid')
            if ev is None or not a or not b: continue
            occ[(a, b)].append((p, k, ev, kind_of(r)))
    at = datetime.date.today().isoformat(); src = src or os.environ.get('DIETS_SRC') or 'pack'
    new = {}; conflicts = []
    for pair, lst in sorted(occ.items()):
        evs = collections.Counter(json.dumps(x[2], ensure_ascii=False) for x in lst); ks = collections.Counter(x[3] for x in lst)
        if len(evs) > 1 or len(ks) > 1: conflicts.append((pair, len(evs), len(ks), len(lst), dict(evs), dict(ks), sorted({os.path.basename(x[0])[:-5] for x in lst})))
        if pair in t: continue
        e = {'ev': json.loads(evs.most_common(1)[0][0]), 'k': ks.most_common(1)[0][0]}   # the most common value; a tie goes to the first place seen
        if not legacy: e |= {'src': src, 'at': at}
        new[pair] = e
    t.update(new)
    stripped = 0; changed = 0; nulls = 0
    for p, d in places.items():
        ev = d.get('ev') or {}; n0 = len(ev); before = json.dumps(ev, ensure_ascii=False)
        for pair, lst in occ.items():
            for (pp, k, e, kind) in lst:
                if pp == p and k in ev and t[pair]['ev'] == e: del ev[k]
        nm = {n['id']: n.get('sp') for n in d['nodes']}
        for r in d['raw']:
            k = r[0] + '>' + r[1]
            if legacy and kind_of(r) in EATS and k not in ev:   # only in the one-off: from then on an absent entry means "as in the table"
                a, b = (tab.get(nm.get(r[0])) or {}).get('sid'), (tab.get(nm.get(r[1])) or {}).get('sid')
                if (a, b) in t and not any(pp == p and kk == k for (pp, kk, _e, _k) in occ.get((a, b), ())) : ev[k] = None; nulls += 1
        if json.dumps(ev, ensure_ascii=False) != before:
            stripped += max(0, n0 - len(ev)); changed += 1
            if not check: d['ev'] = ev; open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
    if not check and new:
        by = collections.defaultdict(dict)
        for (a, b), e in new.items(): by[b][a] = e
        for b, prey in by.items():
            p = path_of(b, root); os.makedirs(os.path.dirname(p), exist_ok=True)
            o = json.load(open(p)) if os.path.exists(p) else {'sid': b, 'prey': {}}
            o['prey'].update(prey); o['prey'] = dict(sorted(o['prey'].items()))
            json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        _cache.pop(dir_of(root), None)
    return {'pairs_seen': len(occ), 'new_pairs': len(new), 'in_table': len(t), 'ev_dropped': stripped, 'null_marks': nulls, 'places_changed': changed, 'pairs_that_differ': conflicts}



def report(conflicts, out):
    """A readable list of the pairs on which places disagree (the table takes the most common value)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import species
    name = {r['sid']: (r.get('latin') or r['name']) for r in species.table().values()}
    kind_only = [c for c in conflicts if len(c[4]) == 1]; lvl = lambda e: json.loads(e)[0]
    lines = ['# Eating links on which places disagree (%d pairs)' % len(conflicts), '',
             'Written by `python3 build/diets.py pack --legacy --report <file>`. The table takes the most common value; a place that differs keeps its own entry (an override).', '',
             '- same evidence, different kind (eaten as food or scavenged): %d' % len(kind_only),
             '- different evidence: %d (of which the level differs: %d)' % (len(conflicts) - len(kind_only), sum(1 for c in conflicts if len(c[4]) > 1 and len({lvl(e) for e in c[4]}) > 1)), '',
             '| prey | eaten by | places | evidence (count) | kind (count) |', '|---|---|---|---|---|']
    for (a, b), ne, nk, n, evs, ks, pl in sorted(conflicts, key=lambda c: -c[3]):
        lines.append('| %s | %s | %d | %s | %s |' % (name.get(a, a), name.get(b, b), n, '; '.join('%s x%d' % (json.loads(e)[0], c) if len(json.loads(e)) else e for e, c in evs.items()), ', '.join('%s x%d' % kc for kc in ks.items())))
    open(out, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    if sys.argv[1:2] != ['pack']: sys.exit(__doc__)
    s = pack(legacy='--legacy' in sys.argv, check='--check' in sys.argv)
    c = s.pop('pairs_that_differ'); print(s); print('%d pairs have different evidence or kind in different places' % len(c))
    if '--report' in sys.argv: report(c, sys.argv[sys.argv.index('--report') + 1])
