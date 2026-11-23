#!/usr/bin/env python3
"""status_page.py: the data status page (#1061, #887). The deploy runs the read-only audit (build/data_audit.py) on the data in the checkout and publishes
status/index.html (from src/status/index.html) and status/audit.json beside the app, so the page always shows main as deployed. Not part of the app: it is not in the
first view, not linked from the app and not in the service worker's precache. Changes no data."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import data_audit
FLAGS = list(data_audit.FLAGS)

def payload(root=ROOT):
    nodes, rows, dups, S = data_audit.audit(root)
    return {
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
