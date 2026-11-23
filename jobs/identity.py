#!/usr/bin/env python3
"""identity.py (#1061, option 5): READ-ONLY. Maps every row (taxon, group, resource) to the Wikidata item of its Wikipedia page, so identity can be judged on the item
(one item, one row) instead of on page titles. For each row it records: the item id (QID) or why there is none (page missing, disambiguation page, no row page), the
item's taxon rank (P105, as an item id) and taxon name (P225) when it is a taxon. Writes data/audit/identity.json = {asOf, ranks:{id:label}, rows:{sid:[qid, rank id, taxon name, kind, why]}}.
It changes no row. Needs the web (en.wikipedia.org, www.wikidata.org, through lib/wm.py), so it runs in a GitHub job.
  python3 jobs/identity.py --json data/audit/identity.json [--max N]"""
import json, os, sys, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import species
import rowtitles as RT
WDR = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids='

def rank_of(ids, get):
    """{item id: (rank item id or '', taxon name or '')} from P105 and P225."""
    out = {}; ids = sorted(set(i for i in ids if i))
    for i in range(0, len(ids), 20):
        for k, v in ((get(WDR + '|'.join(ids[i:i + 20])) or {}).get('entities') or {}).items():
            cl = v.get('claims') or {}
            def first(p):
                for c in cl.get(p) or []:
                    val = ((c.get('mainsnak') or {}).get('datavalue') or {}).get('value')
                    if val: return val
            r = first('P105'); t = first('P225')
            out[k] = ((r or {}).get('id', '') if isinstance(r, dict) else '', t if isinstance(t, str) else '')
    return out

def rows_in(root):
    return sorted((r for r in species.table(root).values() if r.get('sid')), key=lambda r: r['sid'])

def decide(rows, get):
    """{sid: [qid, rank id, taxon name, kind, why]}; qid is '' when none and `why` says so."""
    found = RT.titles_of([r['wiki'] for r in rows if r.get('wiki')], get)
    info = rank_of([f[1] for f in found.values() if f], get)
    out = {}
    for r in rows:
        w = r.get('wiki'); f = found.get(w) if w else None
        if not w: q, why = '', 'row has no page'
        elif not f: q, why = '', 'page missing, a disambiguation page or a section redirect'
        elif not f[1]: q, why = '', 'page has no Wikidata item'
        else: q, why = f[1], ''
        rk, tx = info.get(q, ('', '')) if q else ('', '')
        out[r['sid']] = [q, rk, tx, r.get('sk') or '', why]
    return out

def to_json(res, labels, today): return {'asOf': today, 'ranks': labels, 'rows': res}

def main(argv):
    import wm, datetime
    rows = rows_in(ROOT)
    if '--max' in argv: rows = rows[:int(argv[argv.index('--max') + 1])]
    res = decide(rows, wm.get)
    labels = RT.labels_of([v[1] for v in res.values()], wm.get)
    print('%d rows, %d with an item, %d taxa, %d without a page or item' % (len(res), sum(1 for v in res.values() if v[0]), sum(1 for v in res.values() if v[1]), sum(1 for v in res.values() if not v[0])))
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]; os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, 'w', encoding='utf-8') as h: json.dump(to_json(res, labels, datetime.date.today().isoformat()), h, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

if __name__ == '__main__': main(sys.argv[1:])
