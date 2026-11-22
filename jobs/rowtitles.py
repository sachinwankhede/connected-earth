#!/usr/bin/env python3
"""rowtitles.py (#1061, docs/NODE-NAMES.md): READ-ONLY. What would a species row be called, decided from the data in the order of docs/NODE-NAMES.md?
1 the article title when it is a common name; 2 the English label of the article's Wikidata item when the title is only the scientific name (first letter capital);
3 the English common names Wikidata lists for the taxon (P1843): the current name when it is listed, else the first; 4 a current name that is itself a Wikipedia
article other than the row's page is a more specific concept: reported as OWN ARTICLE (a new row or a repoint, never a plain rename). Nothing is written: the report
lists the rows whose name would change with the step that gave the name, the rows with an own article, and the rows no step settles (missing page, disambiguation
page, no name).
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
WDC = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids='   # P1843 = taxon common name
BINOMIAL = re.compile(r'[A-Z][a-z]+( [a-z]+){1,2}$')

def is_scientific(title, row):
    """True when the title is the row's Latin name, its genus alone, or its genus + an epithet: it says what the species is, not what it is called."""
    t = (title or '').strip(); latin = (row.get('latin') or '').strip().lower()
    if not t or not latin: return False
    w = t.lower().split(); lw = latin.split()
    same_epithet = len(w) == 2 and len(lw) >= 2 and w[1] == lw[1] and bool(BINOMIAL.match(t))   # "Acacia tortilis" for Vachellia tortilis: a synonym, still a Latin name
    return t.lower() == latin or t.lower() == lw[0] or (bool(BINOMIAL.match(t)) and w[0] == lw[0]) or same_epithet

def cap(name): return (name or '')[:1].upper() + (name or '')[1:]

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

def commons_of(ids, get):
    """{wikidata id: [English common names]} from P1843 (taxon common name), in the order Wikidata gives them."""
    out = {}; ids = sorted(set(i for i in ids if i))
    for i in range(0, len(ids), 20):
        ents = (get(WDC + '|'.join(ids[i:i + 20])) or {}).get('entities') or {}
        for k, v in ents.items():
            names = []
            for c in ((v.get('claims') or {}).get('P1843') or []):
                val = ((c.get('mainsnak') or {}).get('datavalue') or {}).get('value') or {}
                if val.get('language') == 'en' and val.get('text') and val['text'] not in names: names.append(val['text'])
            if names: out[k] = names
    return out

def taxa_of(ids, get):
    """{wikidata id: taxon name (P225)}."""
    out = {}; ids = sorted(set(i for i in ids if i))
    for i in range(0, len(ids), 20):
        ents = (get(WDC + '|'.join(ids[i:i + 20])) or {}).get('entities') or {}
        for k, v in ents.items():
            for c in ((v.get('claims') or {}).get('P225') or []):
                val = ((c.get('mainsnak') or {}).get('datavalue') or {}).get('value')
                if isinstance(val, str) and val: out[k] = val; break
    return out

def wrong_page(row, taxon):
    """True when the row is a species (taxon row), its page's item names a different taxon (P225) and that is not its Latin name or a genus of it."""
    latin = (row.get('latin') or '').strip().lower(); t = (taxon or '').strip().lower()
    return bool(latin and t and row.get('sk') == 'taxon' and len(latin.split()) >= 2 and t != latin)

def decide(rows, get):
    """[(row, status, proposed, source)]. status: same, change, wrongpage (the page is another taxon: repoint), specific (the current name is its own article: the proposal is that article) or unresolved (the reason is in `source`)."""
    found = titles_of([r['wiki'] for r in rows], get)
    taxa = taxa_of([f[1] for f in found.values() if f], get)
    sci = [r for r in rows if found.get(r['wiki']) and is_scientific(found[r['wiki']][0], r)]
    lab = labels_of([found[r['wiki']][1] for r in sci], get)
    need = [found[r['wiki']][1] for r in sci if not (lab.get(found[r['wiki']][1]) and not is_scientific(cap(lab[found[r['wiki']][1]]), r))]
    com = commons_of(need, get)
    out = []
    for r in rows:
        f = found.get(r['wiki'])
        if not f: out.append((r, 'unresolved', None, 'the page is missing, a disambiguation page or a section')); continue
        title, qid = f
        if wrong_page(r, taxa.get(qid)): out.append((r, 'wrongpage', None, "the page %r is the taxon %r, not %r" % (title, taxa[qid], r.get('latin')))); continue
        if is_scientific(title, r):
            name = cap(lab.get(qid))
            if name and not is_scientific(name, r): src = 'Wikidata label of %s' % qid
            else:
                names = [n for n in (com.get(qid) or []) if not is_scientific(n, r)]; cur = r.get('name')
                keep = next((n for n in names if n == cur or species.same_name(n, cur)), None)
                if keep: name, src = cur, 'listed as a common name on %s' % qid
                elif cur and not is_scientific(cur, r): name, src = cur, 'no preferred common name on Wikipedia or Wikidata (%s): the current name is kept' % qid   # Wikidata's order is not evidence of a better name
                elif names: name, src = cap(names[0]), 'first common name of %s' % qid
                else: out.append((r, 'unresolved', None, 'the title %r and the Wikidata label %r are scientific names and Wikidata lists no English common name' % (title, lab.get(qid)))); continue
        else: name, src = re.sub(r'\s*\([^)]*\)$', '', title) or title, 'article title'   # "Nene (bird)": the bracket only tells pages apart, it is not part of the name
        same = name == r.get('name') or species.same_name(name, r.get('name'))
        out.append((r, 'same' if same else 'change', name, src))
    # step 4: a current name that is a Wikipedia article other than the row's page is a more specific concept
    ask = [r['name'] for r, st, _, _ in out if st == 'change' and r.get('name')]
    own = titles_of(ask, get) if ask else {}
    res = []
    for r, st, n, s in out:
        o = own.get(r.get('name')) if st == 'change' else None
        page = found.get(r['wiki'])
        if o and page and o[0] != page[0]: res.append((r, 'specific', o[0], "its own article, not the row's page %r" % page[0]))
        else: res.append((r, st, n, s))
    return res

def report(res):
    ch = [x for x in res if x[1] == 'change']; un = [x for x in res if x[1] == 'unresolved']; same = [x for x in res if x[1] == 'same']; sp = [x for x in res if x[1] == 'specific']; wp = [x for x in res if x[1] == 'wrongpage']
    lines = ['rows looked at: %d; name already right: %d; would change: %d; own article (new row or repoint): %d; wrong page (repoint): %d; cannot be settled: %d' % (len(res), len(same), len(ch), len(sp), len(wp), len(un)), '', 'WOULD CHANGE (row | now | proposed | from)']
    lines += ['%s | %s | %s | %s' % (r['sid'], r.get('name'), n, s) for r, _, n, s in ch]
    lines += ['', 'OWN ARTICLE (row | now | its article | note)'] + ['%s | %s | %s | %s' % (r['sid'], r.get('name'), n, s) for r, _, n, s in sp]
    lines += ['', 'WRONG PAGE: repoint (row | now | why)'] + ['%s | %s | %s' % (r['sid'], r.get('name'), s) for r, _, _, s in wp]
    lines += ['', 'CANNOT BE SETTLED (row | now | why)'] + ['%s | %s | %s' % (r['sid'], r.get('name'), s) for r, _, _, s in un]
    return '\n'.join(lines)

def main(argv):
    import wm
    rows = scope(ROOT, '--all' in argv)
    if '--max' in argv: rows = rows[:int(argv[argv.index('--max') + 1])]
    print(report(decide(rows, wm.get)))

if __name__ == '__main__': main(sys.argv[1:])
