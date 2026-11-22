#!/usr/bin/env python3
"""rowtitles.py (#1061, docs/NODE-NAMES.md): READ-ONLY. What would a species row be called if its name were the English Wikipedia title of its page?
A row maps to one article (I1). The article title is the common name Wikipedia settled on; when the title is only the scientific name, the English label of the
article's Wikidata item stands in (first letter capital). Nothing is written: the report lists the rows whose name would change, each with the current name,
the proposed one and where it came from, and the rows that cannot be settled (missing page, disambiguation page, no label), for the owner to read.
  python3 jobs/rowtitles.py                 # rows that some place node still names differently (the cleanup scope)
  python3 jobs/rowtitles.py --all           # every taxon and group row
  python3 jobs/rowtitles.py --max N         # first N rows only (a small first run)
Needs the web (en.wikipedia.org and www.wikidata.org, through lib/wm.py), so it runs in a GitHub job."""
import json, os, re, sys, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import species
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')
WP = 'https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=pageprops&ppprop=disambiguation|wikibase_item&titles='
WD = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels&languages=en&ids='
BINOMIAL = re.compile(r'[A-Z][a-z]+( [a-z]+){1,2}$')

def is_scientific(title, row):
    """True when the title is the row's Latin name (or the row's genus + an epithet): it says what the species is, not what it is called."""
    t = (title or '').strip(); latin = (row.get('latin') or '').strip().lower()
    return bool(t) and (t.lower() == latin or (bool(BINOMIAL.match(t)) and bool(latin) and t.split()[0].lower() == latin.split()[0]))

def scope(root, everything=False):
    """[row] to look at: the rows a place node names differently (default), or every taxon and group row."""
    tab = species.table(root); by = {r['sid']: r for r in tab.values() if r.get('sid')}
    if everything: return sorted((r for r in by.values() if r.get('sk') in ('taxon', 'group') and r.get('wiki')), key=lambda r: r['sid'])
    used = set(); d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            r = by.get(n.get('sp'))
            if r and 'name' in n and r.get('sk') in ('taxon', 'group') and r.get('wiki'): used.add(r['sid'])
    return [by[s] for s in sorted(used)]

def titles_of(pages, get):
    """{asked title: (final title, wikidata id) or None when missing, a disambiguation page or a redirect to a section}."""
    out = {}; pages = sorted(set(pages))
    for i in range(0, len(pages), 50):
        chunk = pages[i:i + 50]
        q = (get(WP + urllib.parse.quote('|'.join(chunk), safe='|')) or {}).get('query') or {}
        norm = {x['from']: x['to'] for x in q.get('normalized') or []}
        red = {x['from']: x for x in q.get('redirects') or []}
        got = {p.get('title'): p for p in (q.get('pages') or {}).values()}
        for t in chunk:
            t1 = norm.get(t, t); r = red.get(t1)
            if r and r.get('tofragment'): out[t] = None; continue
            final = r['to'] if r else t1; p = got.get(final)
            props = (p or {}).get('pageprops') or {}
            out[t] = None if not p or 'missing' in p or 'invalid' in p or 'disambiguation' in props else (final, props.get('wikibase_item'))
    return out

def labels_of(ids, get):
    """{wikidata id: English label}."""
    out = {}; ids = sorted(set(i for i in ids if i))
    for i in range(0, len(ids), 50):
        ents = (get(WD + '|'.join(ids[i:i + 50])) or {}).get('entities') or {}
        for k, v in ents.items():
            lab = ((v.get('labels') or {}).get('en') or {}).get('value')
            if lab: out[k] = lab
    return out

def decide(rows, get):
    """[(row, status, proposed, source)]. status: same, change, or unresolved (the reason is in `source`)."""
    found = titles_of([r['wiki'] for r in rows], get)
    lab = labels_of([(found.get(r['wiki']) or (None, None))[1] for r in rows if is_scientific((found.get(r['wiki']) or ('',))[0], r)], get)
    out = []
    for r in rows:
        f = found.get(r['wiki'])
        if not f: out.append((r, 'unresolved', None, 'the page is missing, a disambiguation page or a section')); continue
        title, qid = f
        if is_scientific(title, r):
            name = lab.get(qid)
            if not name: out.append((r, 'unresolved', None, 'the title %r is the scientific name and Wikidata has no English label' % title)); continue
            name = name[:1].upper() + name[1:]; src = 'Wikidata label of %s' % qid
            if is_scientific(name, r): out.append((r, 'unresolved', None, 'the Wikidata label %r is again a scientific name' % name)); continue
        else: name, src = title, 'article title'
        same = name == r.get('name') or species.same_name(name, r.get('name'))
        out.append((r, 'same' if same else 'change', name, src))
    return out

def report(res):
    ch = [x for x in res if x[1] == 'change']; un = [x for x in res if x[1] == 'unresolved']; same = [x for x in res if x[1] == 'same']
    lines = ['rows looked at: %d; name already the article name: %d; would change: %d; cannot be settled: %d' % (len(res), len(same), len(ch), len(un)), '', 'WOULD CHANGE (row | now | proposed | from)']
    lines += ['%s | %s | %s | %s' % (r['sid'], r.get('name'), n, s) for r, _, n, s in ch]
    lines += ['', 'CANNOT BE SETTLED (row | now | why)'] + ['%s | %s | %s' % (r['sid'], r.get('name'), s) for r, _, _, s in un]
    return '\n'.join(lines)

def main(argv):
    import wm
    rows = scope(ROOT, '--all' in argv)
    if '--max' in argv: rows = rows[:int(argv[argv.index('--max') + 1])]
    print(report(decide(rows, wm.get)))

if __name__ == '__main__': main(sys.argv[1:])
