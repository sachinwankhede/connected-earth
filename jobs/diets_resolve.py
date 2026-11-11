#!/usr/bin/env python3
"""diets_resolve.py: make an eating link the same kind in every place (#399).
Usage: diets_resolve.py [--dry] [--min 0.9] [--report FILE]   (--dry writes nothing)
The kind of a link (eaten `e`, scavenged `s`) is a fact about two species, but each place file keeps its own: a row of `raw` is [from, to] for `e` and [from, to, "s"] for `s`.
For every species pair whose places disagree, the majority kind is applied to the places that differ, when the majority is at least `--min` (default 0.9) of the places.
Pairs below that share are listed and left alone: the owner or a source decides those. The evidence level (`ev`) is NOT touched: whether `g`, `ga`, `gf` or `gg` is right
for a pair is a question of the source, not of a vote, so the level differences stay in the report from `python3 build/diets.py pack --legacy --report`.
No network. Run `python3 build/species.py pack` after it (the data job does)."""
import sys, os, json, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); import diets, species
EATS = diets.EATS


def with_kind(r, kind):
    """The row with its kind set: [a, b] for eaten, [a, b, 's'] for scavenged (what the place files use)."""
    return r[:2] if kind == 'e' else r[:2] + ['s']


def resolve(root, min_share=0.9, dry=False):
    """Returns (fixed, left): fixed = [(prey sid, consumer sid, kind, number of rows changed)], left = [(prey sid, consumer sid, {kind: places})]."""
    st = species.table(root); loaded = {}; occ = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(root, 'data', 'places', '*.json'))):
        if os.path.basename(p) in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
        d = json.load(open(p, encoding='utf-8')); loaded[p] = d
        nm = {n['id']: (st.get(n.get('sp')) or {}).get('sid') for n in d.get('nodes', [])}
        for i, r in enumerate(d.get('raw', [])):
            k = diets.kind_of(r)
            if k not in EATS: continue
            a, b = nm.get(r[0]), nm.get(r[1])
            if a and b: occ[(a, b)].append((p, i, k))
    fixed = []; left = []; edits = collections.defaultdict(list)
    for (a, b), lst in sorted(occ.items()):
        c = collections.Counter(k for _, _, k in lst)
        if len(c) < 2: continue
        kind, n = c.most_common(1)[0]
        if len(c.most_common(2)) > 1 and c.most_common(2)[1][1] == n or n / len(lst) < min_share:   # a tie, or no clear majority
            left.append((a, b, dict(c))); continue
        rows = [(p, i) for p, i, k in lst if k != kind]
        for p, i in rows: edits[p].append((i, kind))
        fixed.append((a, b, kind, len(rows)))
    if not dry:
        for p, es in edits.items():
            d = loaded[p]
            for i, kind in es: d['raw'][i] = with_kind(d['raw'][i], kind)
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
        tab = diets.table(root); by = collections.defaultdict(dict)
        for a, b, kind, _n in fixed:
            if (a, b) in tab and tab[(a, b)].get('k') != kind: by[b][a] = kind
        for b, prey in by.items():   # the table's own kind follows (the table takes the most common value, so this is usually already so)
            fp = diets.path_of(b, root); o = json.load(open(fp, encoding='utf-8'))
            for a, kind in prey.items(): o['prey'][a]['k'] = kind
            json.dump(o, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        diets._cache.pop(diets.dir_of(root), None)
    return fixed, left


def report(root, fixed, left):
    st = species.table(root); name = {r['sid']: (r.get('latin') or r['name']) for r in st.values()}
    lines = ['Kind of eating links made the same in every place (#399)', '', 'pairs fixed: %d, place rows changed: %d' % (len(fixed), sum(f[3] for f in fixed)), '',
             '| prey | eaten by | kind now | rows changed |', '|---|---|---|---|']
    lines += ['| %s | %s | %s | %d |' % (name.get(a, a), name.get(b, b), k, n) for a, b, k, n in sorted(fixed, key=lambda f: -f[3])]
    lines += ['', 'pairs left alone (no clear majority): %d' % len(left), '', '| prey | eaten by | places by kind |', '|---|---|---|']
    lines += ['| %s | %s | %s |' % (name.get(a, a), name.get(b, b), ', '.join('%s x%d' % kc for kc in sorted(c.items()))) for a, b, c in left]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    args = sys.argv[1:]; ms = float(args[args.index('--min') + 1]) if '--min' in args else 0.9
    fx, lf = resolve(ROOT, ms, '--dry' in args); text = report(ROOT, fx, lf)
    if '--report' in args: open(args[args.index('--report') + 1], 'w').write(text)
    else: print(text)
