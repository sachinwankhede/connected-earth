#!/usr/bin/env python3
"""Shared species table. data/species/species.json holds one row per species (key = lowercase Latin name):
the usual name, wiki page, icon, description, trophic level, category and badge.
A place file keeps for each species only its id, latin, position (xh) and whatever differs from the shared row.
  python3 build/species.py pack   fold place files into the table and slim them (safe to repeat)
  python3 build/species.py unpack write full nodes back into place files (for inspection)
The build calls join() so the app receives full nodes either way."""
import json, os, re, sys, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, 'data', 'species', 'species.json')
ROWS = os.path.join(ROOT, 'data', 'species', 'rows')   # #276 step 2: one file per species, data/species/rows/<first two letters of sid>/<sid>.json
ORDER = ['id', 'name', 'latin', 'tl', 'xh', 'wiki', 'canonicalWiki', 'desc', 'ic', 'cat', 'badge']
SHARED = ['latin', 'name', 'tl', 'wiki', 'desc', 'ic', 'cat', 'badge']
key = lambda n: (n.get('latin') or n['name']).lower()

GROUP = re.compile(r' spp\.?|,| and |\(|&|/')
def slug(k): return re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-')
def kind_of(k, row):
    """taxon = one kind of organism at any rank (species, genus, family); group = several named together (a genus, 'bacteria, fungi and worms'); resource = a non-living input (soil, rain, sunlight)."""
    if row.get('cat'): return 'resource'
    return 'group' if GROUP.search(k) else 'taxon'
def assign(new, old):
    """Every row gets a stable id (sid) and a kind (sk). An id is given once and never recomputed from the name, so it survives renames and merges."""
    used = {r['sid'] for r in old.values() if r.get('sid')}
    for k in sorted(new):
        o = old.get(k, {})
        sid = o.get('sid')
        if not sid:
            base = slug(k) or 'x'; sid = base; n = 2
            while sid in used: sid = '%s-%d' % (base, n); n += 1
            used.add(sid)
        new[k]['sid'] = sid; new[k]['sk'] = o.get('sk') or kind_of(k, new[k])

def row_path(sid, rows=None):
    rows = rows or ROWS
    return os.path.join(rows, sid[:2], sid + '.json')

def read_rows(rows):
    out = {}
    for d in sorted(os.listdir(rows)):
        for f in sorted(os.listdir(os.path.join(rows, d))):
            if f.endswith('.json'):
                r = json.load(open(os.path.join(rows, d, f)))
                out[(r.get('latin') or r['name']).lower()] = r
    return dict(sorted(out.items()))

def table(root=None):
    """The species table {lowercase Latin name: row}. Read from the row files when data/species/rows/ exists, else from the one old file."""
    root = root or ROOT
    rows = os.path.join(root, 'data', 'species', 'rows')
    if os.path.isdir(rows): return read_rows(rows)
    old = os.path.join(root, 'data', 'species', 'species.json')
    return json.load(open(old)) if os.path.exists(old) else {}

def write_row(r, rows=None):
    p = row_path(r['sid'], rows); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)

def split():
    """One-off: write every row of the old file as its own file (existing rows are marked src 'legacy': who wrote them is not known) and remove the old file."""
    old = json.load(open(TABLE)); n = 0
    for k, r in old.items():
        write_row({**r, 'src': 'legacy'}); n += 1
    os.remove(TABLE)
    print(n, 'row files written; old species.json removed')

def join(eco, tab):
    import diets
    eco = diets.join(eco, tab)   # #256: the evidence of an eating link that the place does not hold itself comes from data/diets/
    out = []
    for n in eco['nodes']:
        if 'sp' in n and n['sp'] not in tab: raise SystemExit('%s: species %s is not in data/species/species.json (run build/species.py pack)' % (eco.get('id'), n['sp']))
        base = {k: v for k, v in tab.get(n['sp'], {}).items() if k not in ('about', 'sid', 'sk', 'src', 'at')} if 'sp' in n else None
        full = {**(base or {}), **{k: v for k, v in n.items() if k not in ('sp', 'no')}}
        for f in n.get('no', []): full.pop(f, None)
        if base and base.get('wiki') and full.get('wiki') and full['wiki'] != base['wiki']:
            full['canonicalWiki'] = base['wiki']
        out.append({k: full[k] for k in ORDER if k in full} | {k: v for k, v in full.items() if k not in ORDER})
    eco['nodes'] = out
    return eco

def load(path):
    return join(json.load(open(path)), table())

def files():
    d = 'data/places'
    names = [f for f in os.listdir(os.path.join(ROOT, d)) if f.endswith('.json') and f not in ('links.json', 'order.json', 'species.json', 'bounds.json')]
    pilot = lambda f: json.load(open(os.path.join(ROOT, d, f))).get('stage') == 'pilot'
    # main places first, then the pilot ones, each sorted by name: the pack counts votes in this order, and a tie goes to the first seen
    for f in sorted(names, key=lambda f: (pilot(f), f)):
        yield os.path.join(ROOT, d, f)

def pack():
    tab = table(); ecos = {}
    for p in files(): ecos[p] = join(json.load(open(p)), tab)   # full nodes
    seen = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for p, e in ecos.items():
        for n in e['nodes']:
            for f in SHARED:
                seen[key(n)][f][json.dumps(n.get(f), ensure_ascii=False)] += 1
    new = {}; old = tab; rows_mode = os.path.isdir(ROWS)
    for k, fs in sorted(seen.items()):
        row = {}
        for f in SHARED:
            v, c = fs[f].most_common(1)[0]
            if v != 'null': row[f] = json.loads(v)
        if old.get(k, {}).get('about'): row['about'] = old[k]['about']
        new[k] = row
    if rows_mode:
        # The row files are the source of truth: an existing row is never rewritten by a vote. Only a species without a row gets one (marked with who made it and when).
        src = os.environ.get('SPECIES_SRC', 'manual'); today = datetime.date.today().isoformat()
        added = {k: {**row, 'src': src, 'at': today} for k, row in new.items() if k not in old}
        new = {k: (old[k] if k in old else added[k]) for k in new}
    assign(new, old)
    for p, e in ecos.items():
        slim = []
        for n in e['nodes']:
            k = key(n); row = new[k]
            s = {'id': n['id'], 'sp': k, 'xh': n['xh']}
            for f in SHARED:
                if n.get(f) == row.get(f): continue
                if f in n: s[f] = n[f]
                else: s.setdefault('no', []).append(f)
            slim.append(s)
        e['nodes'] = slim
        json.dump(e, open(p, 'w'), ensure_ascii=False)
    if rows_mode:
        for k, r in new.items():
            if k not in old: write_row(r)
    else: json.dump(new, open(TABLE, 'w'), indent=1, ensure_ascii=False)
    print(len(new), 'species rows;', sum(len(e['nodes']) for e in ecos.values()), 'place entries')

def clean(t):
    import re
    t = re.sub(r'\s*\((?:[^()]*;[^()]*|[^()]*/[^()]*|[^()]*listen[^()]*)\)', '', t or '')
    t = re.sub(r'\s*\([^()]*(?: or |[A-Z][a-z]+ [a-z]{3,})[^()]*\)', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) > 200:
        cut = t[:200]; i = max(cut.rfind('. '), 0)
        t = t[:i + 1] if i > 60 else cut.rsplit(' ', 1)[0] + '…'
    return t

# Wikipedia titles that land on a page that is not about the species: disambiguation pages, people, towns, myths.
NOT_ABOUT = re.compile(r"may refer to|can refer to|could refer to|share the common name|is a common name that|:\s*$|\b(given name|female name|male name|surname|unincorporated community|census-designated|is a (village|town|city|municipality|commune)|is an? (album|film|song|band|novel|company|television))\b", re.I)
def about():
    tab = table(); src = json.load(open(os.path.join(ROOT, 'data', 'species', 'about.json'))); n = 0
    before = {r['sid']: json.loads(json.dumps(r)) for r in tab.values()}
    for r in tab.values():
        t = clean(src.get(r.get('wiki'), ''))
        if t and len(t) > 30 and not r.get('cat') and not NOT_ABOUT.search(t): r['about'] = t; n += 1
        else: r.pop('about', None)
    if os.path.isdir(ROWS):
        for r in tab.values():
            if r != before[r['sid']]: write_row(r)
    else: json.dump(tab, open(TABLE, 'w'), indent=1, ensure_ascii=False)
    print(n, 'rows have an about line')

if __name__ == '__main__' and sys.argv[1:] == ['pack']: pack()
if __name__ == '__main__' and sys.argv[1:] == ['about']: about()
if __name__ == '__main__' and sys.argv[1:] == ['split']: split()
