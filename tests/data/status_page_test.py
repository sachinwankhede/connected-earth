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
