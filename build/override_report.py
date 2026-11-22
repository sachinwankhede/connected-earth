#!/usr/bin/env python3
"""override_report.py [root] [--all] [--candidates file.json]: read-only (#1061). Lists every place node that keeps a `name` or `wiki` of its own and says what the owner's rule does with it. Nothing is changed.
Owner rules (#1038, #1061): a row maps to one unique Wikipedia page; no node keeps a name or wiki of its own; a separate article (a redirect is not one) gets its own row; no article means the node uses the nearest row.
Outcome for each node override:
  repoint    a row of the same kind already has the page (wiki override) or the name (name-only override): the node points at that row (`sp`) and drops its override
  ambiguous  several rows of the kind already have the page (the shared pages of #1061: "Rain" is the page of many resource rows): which row the node should use is decided when those rows are merged, not here
  new-row    the page has no row: a candidate for jobs/addspecies.py (data-addspecies); if the process refuses it (no licensed picture, no taxonomy, no summary) the node uses the row it has now and drops the override
  nearest    a name-only override: no page of its own, so no row; the node keeps the row it has and drops the name
A title is compared as written (capitals, spaces and underscores ignored). Redirects are NOT followed here (no network): a page that redirects to a page a row already has shows as new-row, and the dry run of data-addspecies reports it as exists once its title is resolved; jobs/cleanwikis.py is the tool that resolves titles.
--candidates writes the new-row pages as a list for `data-addspecies` ({wiki, kind, name, tl, ic, cat?, latin: ''}): a taxon needs its Latin name filled in by a person or from the current row before a run, since no offline source gives it."""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.json')), os.path.dirname(HERE))
sys.path.insert(0, HERE)
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')

def norm(t): return re.sub(r'[\s_]+', ' ', str(t or '')).strip().lower()

def indexes(tab):
    """({(kind, page): {sids}}, {(kind, name): {sids}}): a page or name held by several rows of a kind is ambiguous (classify says so)."""
    pages = collections.defaultdict(set); names = collections.defaultdict(set)
    for sid, r in tab.items():
        if r.get('wiki'): pages[(r.get('sk'), norm(r['wiki']))].add(sid)
        if r.get('name'): names[(r.get('sk'), norm(r['name']))].add(sid)
    return dict(pages), dict(names)

def classify(node, row, sid, pages, names):
    """(outcome, target sid or None, page or None) for one node that has an override; None when it has none."""
    kind = row.get('sk'); w = node.get('wiki'); n = node.get('name')
    if w and norm(w) != norm(row.get('wiki')):
        hit = pages.get((kind, norm(w)), set()) - {sid}
        if len(hit) > 1: return 'ambiguous', None, w
        if hit: return 'repoint', next(iter(hit)), w
        if (kind, norm(w)) not in pages: return 'new-row', None, w
        return None   # the page is the row's own page: nothing to fix (cleanwikis drops such overrides)
    if n and norm(n) != norm(row.get('name')):
        hit = names.get((kind, norm(n)), set()) - {sid}
        if len(hit) > 1: return 'ambiguous', None, n
        if hit: return 'repoint', next(iter(hit)), n
        return 'nearest', None, None
    return None

def scan(root=ROOT, tab=None):
    """[(place id, node id, row sid, kind, has name, has wiki, outcome, target, page)] for every node with an override."""
    import species
    tab = tab if tab is not None else species.table(root); pages, names = indexes(tab); out = []
    d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            if n.get('sp') not in tab or not ('name' in n or 'wiki' in n): continue
            r = tab[n['sp']]; c = classify(n, r, n['sp'], pages, names)
            if c: out.append((f[:-5], n.get('id'), n['sp'], r.get('sk'), 'name' in n, 'wiki' in n, c[0], c[1], c[2]))
    return out

def candidates(rows, tab):
    """One addspecies candidate per new-row page (the first node's row gives kind, trophic level, icon and category)."""
    seen = {}
    for pid, nid, sid, kind, hn, hw, outcome, target, page in rows:
        if outcome != 'new-row': continue
        k = (kind, norm(page))
        if k in seen: continue
        r = tab[sid]; c = {'wiki': page, 'kind': kind, 'name': page, 'tl': r.get('tl', 0), 'ic': r.get('ic'), 'latin': ''}
        if kind == 'resource': c['cat'] = r.get('cat'); c.pop('latin')
        seen[k] = {a: b for a, b in c.items() if b is not None}
    return sorted(seen.values(), key=lambda c: (c['kind'], c['wiki'].lower()))

def summary(rows):
    """Counts: nodes by (kind, outcome) and distinct pages for new-row."""
    out = collections.Counter()
    for _, _, _, kind, hn, hw, outcome, _, page in rows: out[(kind, outcome)] += 1
    return out

if __name__ == '__main__':
    import species
    tab = species.table(ROOT); rows = scan(ROOT, tab); full = '--all' in sys.argv
    print('%d place nodes keep a name or wiki of their own' % len(rows)); s = summary(rows)
    for (kind, outcome), n in sorted(s.items()): print('%-9s %-9s %5d nodes' % (kind, outcome, n))
    cands = candidates(rows, tab); print('%d distinct new-row pages (%s)' % (len(cands), ', '.join('%s %d' % kv for kv in sorted(collections.Counter(c['kind'] for c in cands).items()))))
    by = collections.Counter((r[6], r[3], r[8] or r[7]) for r in rows if r[6] in ('new-row', 'repoint', 'ambiguous'))
    for (outcome, kind, key), n in by.most_common(None if full else 12): print('  %-8s %-8s %-40s %3d nodes' % (outcome, kind, key, n))
    if '--candidates' in sys.argv:
        out = sys.argv[sys.argv.index('--candidates') + 1]; json.dump(cands, open(out, 'w'), indent=1, ensure_ascii=False); print('wrote', out)
