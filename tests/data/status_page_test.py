#!/usr/bin/env python3
"""The data status page (build/status_page.py): the payload has the audit's totals, every override node and every flagged row; the page fetches audit.json and has every element it fills."""
import json, os, re, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import status_page as SP, data_audit
with tempfile.TemporaryDirectory() as d:
    assert SP.write(d) == ['status/index.html', 'status/audit.json']
    a = json.load(open(os.path.join(d, 'status', 'audit.json'))); html = open(os.path.join(d, 'status', 'index.html')).read()
nodes, rows, dups, S = data_audit.audit(ROOT)
assert a['totals'][0]['value'] == S['rows'] == len(rows) and a['totals'][1]['value'] == len(nodes)
assert len(a['overrides']) == sum(1 for n in nodes if n['outcome']) and len(a['dups']) == len(dups)
assert len(a['rows']) == sum(1 for r in rows if any(r[f] for f in data_audit.FLAGS))
assert {f['flag'] for f in a['flags']} == set(data_audit.FLAGS)
ids = set(re.findall(r"\$\('([a-z]+)'\)", html))
have = set(re.findall(r'id="([a-z]+)"', html))
assert ids <= have, 'the page script uses elements it does not have: %r' % sorted(ids - have)
assert "fetch('audit.json'" in html
print('status page ok')

# the web name check (data/audit/rowtitles.json): absent before the first run, otherwise counts by status and only the rows whose name is not already right
assert SP.web(ROOT, rows) is None or isinstance(SP.web(ROOT, rows)['asOf'], str)
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, 'data', 'audit'))
    ids = [r['id'] for r in rows[:3]]
    json.dump({'asOf': '2026-11-23', 'rows': {ids[0]: ['same', 'A', ''], ids[1]: ['change', 'B', 'article title'], ids[2]: ['unresolved', '', 'no name']}}, open(os.path.join(d, 'data', 'audit', 'rowtitles.json'), 'w'))
    w = SP.web(d, rows)
    assert w['asOf'] == '2026-11-23' and {x['status']: x['rows'] for x in w['status']} == {'name already right': 1, 'would be renamed': 1, 'cannot be settled': 1}
    assert [x['id'] for x in w['rows']] == sorted(ids[1:]) and all(x['status'] != 'name already right' for x in w['rows'])
# a row in data/audit/accepted.json is not listed and not counted (owner, 26 Nov)
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, 'data', 'audit'))
    ids = [r['id'] for r in rows[:3]]
    json.dump({'asOf': '2026-11-23', 'rows': {ids[0]: ['wrongpage', '', 'x'], ids[1]: ['change', 'B', 'article title'], ids[2]: ['same', '', '']}}, open(os.path.join(d, 'data', 'audit', 'rowtitles.json'), 'w'))
    json.dump({'names': {ids[0]: 'synonym'}, 'identity': []}, open(os.path.join(d, 'data', 'audit', 'accepted.json'), 'w'))
    w = SP.web(d, rows)
    assert [x['id'] for x in w['rows']] == [ids[1]] and {x['status']: x['rows'] for x in w['status']} == {'name already right': 1, 'would be renamed': 1}, w
assert "$('webcard')" in html and 'd.web' in html
print('web check ok')

# the identity check (data/audit/identity.json): absent before the first run; shared items, groups by view, rows without an item
assert SP.identity(ROOT, rows) is None or isinstance(SP.identity(ROOT, rows)['asOf'], str)
r1 = {'latin': 'Acer spp.'}; r2 = {'latin': 'Abies spectabilis, Juniperus'}; r3 = {'latin': 'Festuca and other grasses'}
assert SP.group_view(r1, ['Q1', 'Q2', 'Acer', 'group', ''], {'Q2': 'genus'}) == SP.VIEWS[2]
assert SP.group_view(r2, ['Q1', 'Q2', 'Abies spectabilis', 'group', ''], {'Q2': 'species'}) == SP.VIEWS[3]
assert SP.group_view(r3, ['Q1', 'Q2', 'Festuca', 'group', ''], {'Q2': 'genus'}) == SP.VIEWS[3]
assert SP.group_view(r1, ['Q1', 'Q2', 'Felidae', 'group', ''], {'Q2': 'family'}) == SP.VIEWS[4]
assert SP.group_view(r1, ['Q1', '', '', 'group', ''], {}) == SP.VIEWS[1] and SP.group_view(r1, ['', '', '', 'group', 'x'], {}) == SP.VIEWS[5]
assert "$('idcard')" in html and 'd.identity' in html
print('identity view ok')

# problems (wrong or unneeded data) are kept apart from missing data (not there yet, pictures included)
ff = a['fixfirst']; P, M = ff['problems'], ff['missing']
assert P and M and all(isinstance(x['count'], int) and x['item'].startswith('#') for x in P + M)
assert {x['what'] for x in P}.isdisjoint({x['what'] for x in M})
assert any('picture' in x['what'].lower() for x in M)
assert any(x['what'] == 'Rows on a Wikipedia page of the wrong rank' and isinstance(x['count'], int) and x['who'] == 'you' for x in P)   # #1142
assert any(x['what'] == 'Node picture entries no place shows' and isinstance(x['count'], int) for x in P)   # orphan node entries are on the Fix first card (#1183)
assert all(x['who'] in ('me', 'job', 'you') for x in P + M) and a['fixfirst']['stats'] and all(isinstance(x['value'], int) for x in a['fixfirst']['stats'])
assert "$('fixlist')" in html and "$('misslist')" in html and "$('statlist')" in html and 'd.fixfirst.problems' in html and 'd.fixfirst.missing' in html
print('problems and missing ok')
