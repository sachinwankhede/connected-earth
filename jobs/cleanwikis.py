#!/usr/bin/env python3
"""cleanwikis.py (#1038 step 2, #887 step 7): a place node keeps a `wiki` page of its own only when it is a different page from its species row's.
For each distinct (row wiki, node wiki) pair this asks Wikipedia where both titles lead (redirects followed, 50 titles a request). When both reach the same existing article, and it is not a disambiguation page, the node drops its `wiki` and the row's wins. A title that is missing, a disambiguation page, or a redirect to a section is left alone, as is any pair the answer does not cover.
  python3 jobs/cleanwikis.py            # rewrite the place files; prints one line per pair dropped and one per pair kept
  python3 jobs/cleanwikis.py --dry      # same lookups, writes nothing
  python3 jobs/cleanwikis.py --max N    # look up at most N pairs (a first small run)
Needs the web (en.wikipedia.org, through lib/wm.py), so it runs in a GitHub job. Only the nodes' own `wiki` field changes."""
import json, os, sys, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import species
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')
API = 'https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=pageprops&ppprop=disambiguation&titles='

def lookup(titles, get):
    """{title as asked: final article title, or None when it is missing, a disambiguation page or a redirect to a section}."""
    out = {}; titles = sorted(set(titles))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = (get(API + urllib.parse.quote('|'.join(chunk), safe='')) or {}).get('query') or {}
        norm = {x['from']: x['to'] for x in q.get('normalized') or []}
        red = {x['from']: x for x in q.get('redirects') or []}
        pages = {p.get('title'): p for p in (q.get('pages') or {}).values()}
        for t in chunk:
            t1 = norm.get(t, t); r = red.get(t1)
            if r and r.get('tofragment'): out[t] = None; continue
            final = r['to'] if r else t1
            p = pages.get(final)
            out[t] = final if p and 'missing' not in p and 'invalid' not in p and 'pageprops' not in p else None
    return out

def pairs(root):
    by = {r['sid']: r for r in species.table(root).values() if r.get('sid')}; found = {}
    d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            row = by.get(n.get('sp'))
            if row and n.get('wiki') and row.get('wiki'): found[(row['wiki'], n['wiki'])] = 1
    return sorted(found)

def decide(ps, get):
    """{pair: True when the node's wiki is the row's page}."""
    got = lookup([t for p in ps for t in p], get)
    return {p: bool(got.get(p[0])) and got.get(p[0]) == got.get(p[1]) for p in ps}

def apply(root, same, dry=False):
    by = {r['sid']: r for r in species.table(root).values() if r.get('sid')}; total = files = 0; d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in SKIP: continue
        p = os.path.join(d, f); e = json.load(open(p))
        if not isinstance(e, dict): continue
        n = 0
        for node in e.get('nodes') or []:
            row = by.get(node.get('sp'))
            if row and node.get('wiki') and same.get((row.get('wiki'), node['wiki'])): del node['wiki']; n += 1
        if n:
            total += n; files += 1
            if not dry: json.dump(e, open(p, 'w'), ensure_ascii=False)
    return total, files

def main(argv):
    import wm
    dry = '--dry' in argv; ps = pairs(ROOT)
    if '--max' in argv: ps = ps[:int(argv[argv.index('--max') + 1])]
    same = decide(ps, wm.get)
    for p in ps: print(('drop  ' if same[p] else 'keep  ') + '%s | %s' % p)
    total, files = apply(ROOT, {p: v for p, v in same.items() if v}, dry)
    print('%d of %d pairs are the row\'s own page; %d wiki overrides dropped in %d place files%s' % (sum(same.values()), len(ps), total, files, ' (dry run)' if dry else ''))

if __name__ == '__main__': main(sys.argv[1:])
