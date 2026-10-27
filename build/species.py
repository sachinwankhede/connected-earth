#!/usr/bin/env python3
"""Shared species table. data/species.json holds one row per species (key = lowercase Latin name):
the usual name, wiki page, icon, description, trophic level, category and badge.
A place file keeps for each species only its id, latin, position (xh) and whatever differs from the shared row.
  python3 build/species.py pack   fold place files into the table and slim them (safe to repeat)
  python3 build/species.py unpack write full nodes back into place files (for inspection)
The build calls join() so the app receives full nodes either way."""
import json, os, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, 'data', 'species.json')
ORDER = ['id', 'name', 'latin', 'tl', 'xh', 'wiki', 'desc', 'ic', 'cat', 'badge']
SHARED = ['latin', 'name', 'tl', 'wiki', 'desc', 'ic', 'cat', 'badge']
key = lambda n: (n.get('latin') or n['name']).lower()

def table():
    return json.load(open(TABLE)) if os.path.exists(TABLE) else {}

def join(eco, tab):
    out = []
    for n in eco['nodes']:
        if 'sp' in n and n['sp'] not in tab: raise SystemExit('%s: species %s is not in data/species.json (run build/species.py pack)' % (eco.get('id'), n['sp']))
        base = {k: v for k, v in tab.get(n['sp'], {}).items() if k != 'about'} if 'sp' in n else None
        full = {**(base or {}), **{k: v for k, v in n.items() if k not in ('sp', 'no')}}
        for f in n.get('no', []): full.pop(f, None)
        out.append({k: full[k] for k in ORDER if k in full} | {k: v for k, v in full.items() if k not in ORDER})
    eco['nodes'] = out
    return eco

def load(path):
    return join(json.load(open(path)), table())

def files():
    for d in ('data', 'data-auto'):
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            if f.endswith('.json') and f not in ('links.json', 'order.json', 'species.json'):
                yield os.path.join(ROOT, d, f)

def pack():
    tab = table(); ecos = {}
    for p in files(): ecos[p] = join(json.load(open(p)), tab)   # full nodes
    seen = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for p, e in ecos.items():
        for n in e['nodes']:
            for f in SHARED:
                seen[key(n)][f][json.dumps(n.get(f), ensure_ascii=False)] += 1
    new = {}; old = tab
    for k, fs in sorted(seen.items()):
        row = {}
        for f in SHARED:
            v, c = fs[f].most_common(1)[0]
            if v != 'null': row[f] = json.loads(v)
        if old.get(k, {}).get('about'): row['about'] = old[k]['about']
        new[k] = row
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
    json.dump(new, open(TABLE, 'w'), indent=1, ensure_ascii=False)
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

def about():
    tab = table(); src = json.load(open(os.path.join(ROOT, 'pipeline', 'about.json'))); n = 0
    for r in tab.values():
        t = clean(src.get(r.get('wiki'), ''))
        if t and len(t) > 30 and not r.get('cat'): r['about'] = t; n += 1
        else: r.pop('about', None)
    json.dump(tab, open(TABLE, 'w'), indent=1, ensure_ascii=False)
    print(n, 'rows have an about line')

if __name__ == '__main__' and sys.argv[1:] == ['pack']: pack()
if __name__ == '__main__' and sys.argv[1:] == ['about']: about()
