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
assert "$('webcard')" in html and 'd.web' in html
print('web check ok')
