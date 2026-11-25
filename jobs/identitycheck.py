#!/usr/bin/env python3
"""identitycheck.py (#1142, step a, species half): READ-ONLY. Lists the taxon rows whose Wikipedia page is at the wrong rank for the row, from data/audit/identity.json (jobs/identity.py):
a species row (two or more words in its Latin name) on a page of genus rank or higher, and a genus row (one word) on a page of species rank. A different accepted name for the same species
(a synonym, e.g. Abaeis nicippe / Eurema nicippe) is NOT listed: it is the same animal. Writes data/audit/identity_mismatch.json = {asOf, rows:{sid:[reason, latin, page taxon, page rank]}} and removes nothing;
the owner decides what to remove (strictrows). Offline: reads the checkout only.
  python3 jobs/identitycheck.py [--json data/audit/identity_mismatch.json]"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
ABOVE = {'genus', 'subgenus', 'tribe', 'subtribe', 'subfamily', 'family', 'superfamily', 'order', 'suborder', 'class', 'subclass', 'phylum', 'division', 'kingdom'}
SPECIES = {'species', 'subspecies', 'variety', 'nothospecies'}

def mismatches(rows, ident):
    """{sid: [reason, latin, page taxon, page rank]} for rows {sid: row with 'latin'}; ident = identity.json content."""
    lab = ident.get('ranks') or {}; out = {}
    for sid, v in (ident.get('rows') or {}).items():
        r = rows.get(sid)
        if not r or v[3] != 'taxon' or not v[0]: continue
        words = len((r.get('latin') or '').split()); rank = lab.get(v[1], '')
        if words >= 2 and rank in ABOVE: out[sid] = ['species row on a %s page' % rank, r.get('latin'), v[2], rank]
        elif words == 1 and rank in SPECIES: out[sid] = ['genus row on a %s page' % rank, r.get('latin'), v[2], rank]
    return out

def main(argv):
    import species, datetime
    ident = json.load(open(os.path.join(ROOT, 'data', 'audit', 'identity.json'), encoding='utf-8'))
    rows = {r['sid']: r for r in species.table(ROOT).values() if r.get('sid')}
    res = mismatches(rows, ident)
    by = {}
    for v in res.values(): by[v[0]] = by.get(v[0], 0) + 1
    print('%d mismatches: %s' % (len(res), ', '.join('%s %d' % (k, n) for k, n in sorted(by.items()))))
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
        with open(out, 'w', encoding='utf-8') as h: json.dump({'asOf': datetime.date.today().isoformat(), 'identityAsOf': ident.get('asOf'), 'rows': res}, h, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

if __name__ == '__main__': main(sys.argv[1:])
