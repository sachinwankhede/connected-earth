#!/usr/bin/env python3
"""status_page.py: the data status page (#1061, #887). The deploy runs the read-only audit (build/data_audit.py) on the data in the checkout and publishes
status/index.html (from src/status/index.html) and status/audit.json beside the app, so the page always shows main as deployed. Not part of the app: it is not in the
first view, not linked from the app and not in the service worker's precache. Changes no data."""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import data_audit
FLAGS = list(data_audit.FLAGS)

def web(root, rows):
    """The web name check (data/audit/rowtitles.json, written by the data-rowtitles job), or None before its first run: counts by status and the rows whose name is not already right."""
    path = os.path.join(root, 'data', 'audit', 'rowtitles.json')
    if not os.path.exists(path): return None
    d = json.load(open(path, encoding='utf-8')); by = {r['id']: r for r in rows}; res = d.get('rows') or {}
    names = {'same': 'name already right', 'change': 'would be renamed', 'repoint': 'own article, same species (repoint the page)', 'newrow': 'own article, other species (new row)', 'specific': 'own article, check by hand', 'wrongpage': 'wrong page (repoint)', 'unresolved': 'cannot be settled'}
    count = collections.Counter(v[0] for v in res.values())
    return {'asOf': d.get('asOf'), 'status': [{'status': names[k], 'rows': count[k]} for k in names if count[k]],
            'rows': [{'id': k, 'name': (by.get(k) or {}).get('name', ''), 'page': (by.get(k) or {}).get('page', ''), 'status': names.get(v[0], v[0]), 'proposed': v[1], 'why': v[2]} for k, v in sorted(res.items()) if v[0] != 'same']}

VIEWS = ['shared item (one item, several rows)', 'group: role-based, stays', 'group: convert candidate (members all in the page taxon)', 'group: keep (members go beyond the page taxon)', 'group: needs a person (page is a higher rank)', 'group: no page or item', 'row without an item']

def group_view(r, v, ranks):
    """Which view a group row falls in, from its item (v = [qid, rank id, taxon name, kind, why]) and its `latin` member list (a text check, not a decision)."""
    if not v[0]: return VIEWS[5]
    if not v[1]: return VIEWS[1]
    rk = ranks.get(v[1], v[1])
    if rk not in ('genus', 'species'): return VIEWS[4]
    parts = [x.strip() for x in re.split(r',|;| and | & ', re.sub(r'\b(and relatives|spp?\.?|etc\.?|relatives)\b', '', r.get('latin') or '')) if x.strip()]
    gen = {x.split()[0] for x in parts if re.match(r'[A-Z][a-z]+', x)}; g0 = (v[2] or '').split(' ')[0]
    if not gen or 'other' in (r.get('latin') or '').lower(): return VIEWS[4] if not gen else VIEWS[3]
    return VIEWS[2] if gen == {g0} and (rk == 'genus' or all(x == v[2] for x in parts)) else VIEWS[3]

def identity(root, rows):
    """The identity check (data/audit/identity.json, written by the data-identity job), or None before its first run: the Wikidata item of every row's page. Lists the items several rows share, the groups by what a text check says, and the rows with no item."""
    path = os.path.join(root, 'data', 'audit', 'identity.json')
    if not os.path.exists(path): return None
    d = json.load(open(path, encoding='utf-8')); R = d.get('rows') or {}; ranks = d.get('ranks') or {}; by = {r['id']: r for r in rows}
    import species
    full = {r['sid']: r for r in species.table(root).values() if r.get('sid')}
    cl = collections.defaultdict(list)
    for k, v in R.items():
        if v[0]: cl[v[0]].append(k)
    out = []
    for q, m in sorted(cl.items()):
        if len(m) > 1: out.append({'view': VIEWS[0], 'item': q, 'kinds': ' '.join(sorted({R[k][3] for k in m})), 'ids': ' '.join(sorted(m)), 'names': ', '.join((full.get(k) or {}).get('name', '') for k in sorted(m)), 'detail': (R[m[0]][2] or '')})
    for k, v in sorted(R.items()):
        r = full.get(k) or {}
        if v[3] == 'group': out.append({'view': group_view(r, v, ranks), 'item': v[0], 'kinds': 'group', 'ids': k, 'names': r.get('name', ''), 'detail': '%s | %s | %s' % (ranks.get(v[1], ''), v[2], r.get('latin', ''))})
        elif not v[0]: out.append({'view': VIEWS[6], 'item': '', 'kinds': v[3], 'ids': k, 'names': r.get('name', ''), 'detail': v[4]})
    n = collections.Counter(x['view'] for x in out)
    return {'asOf': d.get('asOf'), 'rowsChecked': len(R), 'views': [{'view': k, 'rows': n[k]} for k in VIEWS if n[k]], 'rows': out}

def fixfirst(root, S, rows):
    """Two lists, kept apart (owner, 24 Nov, #1061): `problems` is data that is wrong or unneeded (fix first: correct or delete) and `missing` is data not there yet (add after). Counts are read from the checkout (place files, data/audit/strictrows.json, the audit rows, build/data_status.py), so they are as fresh as the deploy. Each line names its item."""
    import species, data_status
    d = os.path.join(root, 'data', 'places'); no_env = 0; places = 0
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in data_audit.SKIP: continue
        try: e = species.load(os.path.join(d, f))
        except Exception: continue
        if not isinstance(e, dict) or 'nodes' not in e: continue
        places += 1; cats = {n.get('cat') for n in e['nodes']}
        if 'abiotic' not in cats or 'decomp' not in cats: no_env += 1
    sp = os.path.join(root, 'data', 'audit', 'strictrows.json'); sr = json.load(open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
    ids = {r['id'] for r in rows}
    journey = sorted(k for k, v in (sr.get('kept') or {}).items() if 'journey ends' in v and k in ids)   # a row merged or removed since is no longer a problem
    def ex(flag): return ', '.join('%s (%s)' % (r['name'], r['id']) for r in [r for r in rows if r[flag]][:2])
    fl = S['row_flags']; ds = {r['dataset']: r for r in data_status.rows(root)}
    doubts = sum(r['doubts'] for r in ds.values())
    sp_rows = sum(1 for r in rows if r['kind'] in ('taxon', 'group'))
    # who: job = a data job fixes it, me = Claude fixes it in a pull request, you = needs the owner's decision
    problems = [
        {'what': 'Two rows with the same name', 'count': fl['shared_name'], 'example': ex('shared_name'), 'fix': 'rename one to its own page title', 'item': '#1142', 'who': 'me'},
        {'what': 'Row name does not match its own Wikipedia page', 'count': fl['name_breaks_rule'], 'example': ex('name_breaks_rule'), 'fix': 'rename to the page title, or delete the row', 'item': '#1061', 'who': 'me'},
        {'what': 'Row name not yet checked on the web', 'count': fl['name_unchecked'], 'example': ex('name_unchecked'), 'fix': 'apply the name the web check found, or run the web check', 'item': '#1061', 'who': 'me'},
        {'what': 'Rows no place uses', 'count': fl['no_node'], 'example': ex('no_node'), 'fix': 'delete (nothing shows them)', 'item': '#1061', 'who': 'job'},
        {'what': 'Two rows on one Wikipedia page', 'count': fl['shared_page'], 'example': ex('shared_page'), 'fix': 'merge into one row or repoint', 'item': '#1142', 'who': 'me'},
        {'what': 'Wrong rows kept because a journey ends at their node', 'count': len(journey), 'example': ', '.join(journey) or 'none', 'fix': 'change the journey or drop the row', 'item': '#1142', 'who': 'you'},
        {'what': 'Pictures credited to an unknown author', 'count': doubts, 'example': 'places, species and nodes', 'fix': 'find the author or remove the picture (licence doubt)', 'item': '#887', 'who': 'you'},
    ]
    missing = [
        {'what': 'Places with no abiotic or no decomposer node', 'count': no_env, 'have': '%d of %d places' % (places - no_env, places), 'done': places - no_env, 'total': places, 'fix': 'add accurate nodes, then make the rule strict again', 'item': '#1138', 'who': 'me'},
        {'what': 'Places removed by the cleanup', 'count': len(sr.get('places') or {}), 'have': 'to recreate', 'fix': 'add the places back with accurate rows', 'item': '#1132', 'who': 'job'},
        {'what': 'Species without an "about" text', 'count': fl['no_about'], 'have': '%d of %d have one' % (sp_rows - fl['no_about'], sp_rows), 'done': sp_rows - fl['no_about'], 'total': sp_rows, 'fix': 'write it', 'item': '#1061', 'who': 'job'},
    ] + [{'what': n + ' missing', 'count': ds[k]['missing'], 'have': '%d of %d have one' % (ds[k]['have'], ds[k]['items']), 'done': ds[k]['have'], 'total': ds[k]['items'], 'fix': 'the weekly job retries', 'item': '#887', 'who': 'job'} for k, n in (('Place pictures', 'Place pictures'), ('Species pictures', 'Species pictures'), ('Node pictures', 'Node pictures'), ('Outlines', 'Place outlines'), ('Stories', 'Place stories')) if k in ds and ds[k]['missing']]
    kinds = S['rows_by_kind']
    stats = [{'label': 'Places', 'value': places}, {'label': 'Species and groups', 'value': sp_rows}, {'label': 'Other rows (soil, sun, water...)', 'value': sum(1 for r in rows) - sp_rows}, {'label': 'Place nodes', 'value': S['nodes']}]
    stats += [{'label': k, 'value': ds[k]['have'], 'of': ds[k]['items']} for k in ('Place pictures', 'Species pictures') if k in ds]
    return {'problems': problems, 'missing': missing, 'stats': stats}

def payload(root=ROOT):
    nodes, rows, dups, S = data_audit.audit(root)
    return {
        'fixfirst': fixfirst(root, S, rows),
        'web': web(root, rows),
        'identity': identity(root, rows),
        'totals': [{'metric': 'Species rows', 'value': S['rows']}, {'metric': 'Place nodes', 'value': S['nodes']},
                   {'metric': 'Nodes with own name or page', 'value': S['nodes_with_override']}, {'metric': 'Nodes on a missing row', 'value': S['nodes_pointing_at_a_missing_row']}],
        'kinds': [{'kind': k, 'rows': v} for k, v in S['rows_by_kind'].items()],
        'flags': [{'flag': k, 'meaning': S['flag_meaning'][k], 'rows': S['row_flags'][k]} for k in FLAGS],
        'outcomes': [{'outcome': k, 'nodes': v} for k, v in S['nodes_by_outcome'].items() if k != 'no override'],
        'dups': dups,
        'overrides': [{k: n[k] for k in ('place', 'node', 'sp', 'node_name', 'node_page', 'row_name', 'row_page', 'row_kind', 'outcome', 'target_row')} for n in nodes if n['outcome']],
        'rows': [{'id': r['id'], 'kind': r['kind'], 'name': r['name'], 'page': r['page'], 'nodes': r['nodes'], 'places': r['places'], 'flags': ' '.join(f for f in FLAGS if r[f])} for r in rows if any(r[f] for f in FLAGS)],
    }

def write(dest, root=ROOT):
    """Write dest/status/index.html and dest/status/audit.json; return the two relative paths."""
    out = os.path.join(dest, 'status'); os.makedirs(out, exist_ok=True)
    with open(os.path.join(root, 'src', 'status', 'index.html'), encoding='utf-8') as h: html = h.read()
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as h: h.write(html)
    with open(os.path.join(out, 'audit.json'), 'w', encoding='utf-8') as h: json.dump(payload(root), h, ensure_ascii=False, separators=(',', ':'))
    return ['status/index.html', 'status/audit.json']

if __name__ == '__main__':
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'status-preview'); print(write(dest), dest)
