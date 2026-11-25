#!/usr/bin/env python3
"""data_audit.py [--out DIR]: READ-ONLY, offline. The detail behind the data status table (#1061, #887): every place node, every species row, every row that shares a page, name or Latin name with another, and the counts.
Writes to DIR (default audit/): nodes.csv, rows.csv, duplicates.csv, summary.json. It changes no data. A reader can sort nodes.csv by `outcome` to see what the cleanup still has to settle.
  nodes.csv       one line per place node: place, node, species id, the name and page the node overrides with (empty = it follows its row), the row's own name, page, Latin name and kind,
                  and `outcome` (override_report.classify: repoint, new-row, nearest, ambiguous, place, cross-kind; empty = no override).
  rows.csv        one line per species row: id, kind, name, page, Latin name, trophic level, how many nodes and places use it, and a flag per problem (see FLAGS).
  duplicates.csv  rows that share a page, a name or a Latin name: what, the shared value, the row ids.
Run from the repository root. Pictures, outlines and records are in build/data_status.py; the web checks (is the row's page the right species, is its name the page title) are jobs/rowtitles.py."""
import collections, csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import species, override_report as OR

SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')
FLAGS = {
    'no_page': 'the row has no Wikipedia page (`wiki`)',
    'no_latin': 'a taxon without a Latin name',
    'name_breaks_rule': 'the page title is a common name (brackets dropped), the row name differs from it and the web name check did not find the name already right: a rename, or a more specific concept that needs its own row (docs/NODE-NAMES.md steps 1 and 4)',
    'name_unchecked': 'the page title is only a Latin name, so the right name is the Wikidata label (step 2): jobs/rowtitles.py checks it on the web, the offline audit cannot. A row the web check has settled (name already right, or no common name exists) is not listed; one it proposes another name for, and one it has not seen, is',
    'shared_page': 'another row of the same kind has the same page',
    'shared_name': 'another row of the same kind has the same name',
    'shared_latin': 'another taxon row has the same Latin name',
    'no_node': 'no place node uses the row',
    'no_about': 'a taxon or group without a description (`about`)',
}

def norm(t): return OR.norm(t)
def plain(t): return norm(re.sub(r'\s*\([^()]*\)\s*$', '', str(t or '')))   # "Nene (bird)" gives "nene"
def scientific(title, row):
    """The same test as jobs/rowtitles.is_scientific (kept here so this audit stays offline and imports nothing from jobs/)."""
    t = (title or '').strip(); latin = (row.get('latin') or '').strip().lower()
    if not t or not latin: return False
    w = t.lower().split(); lw = latin.split(); binom = bool(re.match(r'[A-Z][a-z]+( [a-z]+){1,2}$', t))
    return t.lower() == latin or t.lower() == lw[0] or (binom and w[0] == lw[0]) or (len(w) == 2 and len(lw) >= 2 and w[1] == lw[1] and binom)

def place_nodes(root):
    d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        if isinstance(e, dict):
            for n in e.get('nodes') or []: yield f[:-5], n

def web_rows(root):
    """{id: [status, proposed name, why]} of the web name check (data/audit/rowtitles.json), or {} when it has not run."""
    p = os.path.join(root, 'data', 'audit', 'rowtitles.json')
    return (json.load(open(p, encoding='utf-8')).get('rows') or {}) if os.path.exists(p) else {}

def web_same(root):
    """Ids whose name the web name check (data/audit/rowtitles.json) found already right: a listed common name of the row's page, not a break of the rule (owner, 24 Nov, #1061: Wolf on the page Gray wolf)."""
    p = os.path.join(root, 'data', 'audit', 'rowtitles.json')
    if not os.path.exists(p): return set()
    return {k for k, v in (json.load(open(p, encoding='utf-8')).get('rows') or {}).items() if v and v[0] == 'same'}

def audit(root=ROOT):
    tab = species.table(root); same = web_same(root); web = web_rows(root)
    out_nodes = []; use = collections.Counter(); places = collections.defaultdict(set)
    over = {(p, n): (c, t, pg) for p, n, _sid, _k, _hn, _hw, c, t, pg in OR.scan(root, tab)}
    for pid, n in place_nodes(root):
        sid = n.get('sp'); r = tab.get(sid) or {}
        use[sid] += 1; places[sid].add(pid)
        c = over.get((pid, n.get('id')))
        out_nodes.append({'place': pid, 'node': n.get('id'), 'sp': sid, 'node_name': n.get('name', ''), 'node_page': n.get('wiki', ''),
                          'row_name': r.get('name', ''), 'row_page': r.get('wiki', ''), 'row_latin': r.get('latin', ''), 'row_kind': r.get('sk', '') if r else 'MISSING ROW',
                          'outcome': c[0] if c else '', 'target_row': c[1] or '' if c else '', 'target_page': c[2] or '' if c else ''})
    by_page = collections.defaultdict(list); by_name = collections.defaultdict(list); by_latin = collections.defaultdict(list)
    for sid, r in tab.items():
        if r.get('wiki'): by_page[(r.get('sk'), norm(r['wiki']))].append(sid)
        if r.get('name'): by_name[(r.get('sk'), norm(r['name']))].append(sid)
        if r.get('latin') and r.get('sk') == 'taxon': by_latin[norm(r['latin'])].append(sid)
    out_rows = []
    for sid, r in sorted(tab.items()):
        kind = r.get('sk'); page = r.get('wiki') or ''; name = r.get('name') or ''
        f = {
            'no_page': not page,
            'no_latin': kind == 'taxon' and not r.get('latin'),
            'name_breaks_rule': bool(page) and kind in ('taxon', 'group') and not scientific(page, r) and plain(name) != plain(page) and sid not in same,
            'name_unchecked': bool(page) and kind in ('taxon', 'group') and scientific(page, r) and (sid not in web or (web[sid][0] in ('change', 'wrongpage', 'specific', 'repoint', 'newrow') and plain(name) != plain(web[sid][1] or name))),
            'shared_page': bool(page) and len(by_page.get((kind, norm(page)), [])) > 1,
            'shared_name': bool(name) and len(by_name.get((kind, norm(name)), [])) > 1,
            'shared_latin': kind == 'taxon' and bool(r.get('latin')) and len(by_latin.get(norm(r['latin']), [])) > 1,
            'no_node': use[sid] == 0,
            'no_about': kind in ('taxon', 'group') and not r.get('about'),
        }
        out_rows.append(dict({'id': sid, 'kind': kind, 'name': name, 'page': page, 'latin': r.get('latin') or '', 'tl': r.get('tl', ''), 'nodes': use[sid], 'places': len(places[sid]), 'source': r.get('src', '')},
                             **{k: int(v) for k, v in f.items()}))
    dups = []
    for what, groups in (('page', by_page), ('name', by_name), ('latin', by_latin)):
        for key, sids in sorted(groups.items(), key=lambda kv: str(kv[0])):
            if len(sids) > 1: dups.append({'what': what, 'kind': key[0] if what != 'latin' else 'taxon', 'value': key[-1], 'rows': ' '.join(sorted(sids)), 'nodes': sum(use[s] for s in sids)})
    missing_rows = collections.Counter(n['sp'] for n in out_nodes if n['row_kind'] == 'MISSING ROW')
    summary = {
        'rows': len(tab), 'rows_by_kind': dict(collections.Counter(r.get('sk') for r in tab.values())),
        'nodes': len(out_nodes), 'nodes_with_override': sum(1 for n in out_nodes if n['node_name'] or n['node_page']),
        'nodes_by_outcome': dict(collections.Counter(n['outcome'] or 'no override' for n in out_nodes)),
        'nodes_pointing_at_a_missing_row': sum(missing_rows.values()),
        'row_flags': {k: sum(r[k] for r in out_rows) for k in FLAGS}, 'flag_meaning': FLAGS,
        'duplicate_groups': dict(collections.Counter(d['what'] for d in dups)),
    }
    return out_nodes, out_rows, dups, summary

def write(out, nodes, rows, dups, summary):
    os.makedirs(out, exist_ok=True)
    for name, data in (('nodes', nodes), ('rows', rows), ('duplicates', dups)):
        with open(os.path.join(out, name + '.csv'), 'w', newline='', encoding='utf-8') as h:
            if data:
                w = csv.DictWriter(h, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as h: json.dump(summary, h, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, 'audit')
    nodes, rows, dups, summary = audit(ROOT); write(out, nodes, rows, dups, summary)
    print(json.dumps(summary, indent=1, ensure_ascii=False)); print('wrote', out)
