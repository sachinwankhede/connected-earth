#!/usr/bin/env python3
"""journeys.py: rank candidate journeys (docs/JOURNEYS.md, "Finding more journeys") into research/journey-candidates.md.

A candidate is a species that lives in places at least 2,500 km apart AND whose Wikipedia article says it migrates
(a "migrat..." category, or the word in the lead). Residents such as deer, coyote and raven drop out. Ranked by how clear the
evidence is, then by distance, then by how many places it is in. Species that already have a journey are marked.
Needs the web (Wikipedia), so it runs in a GitHub job (data-journeys). JOURNEYS_OFFLINE=1 skips the web (all evidence 'unknown')."""
import glob, json, math, os, re, sys, urllib.parse
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, here)
OFFLINE = bool(os.environ.get('JOURNEYS_OFFLINE')); MIN_KM = 2500; TOP = 50

def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def load():
    tab = json.load(open(os.path.join(ROOT, 'data', 'species.json')))
    places = []
    for d in ('data', 'data-auto'):
        for f in sorted(glob.glob(os.path.join(ROOT, d, '*.json'))):
            if f.endswith(('order.json', 'links.json', 'species.json', 'bounds.json')): continue
            try: e = json.load(open(f))
            except Exception: continue
            if isinstance(e, dict) and e.get('nodes'): places.append(e)
    links = json.load(open(os.path.join(ROOT, 'data', 'links.json')))
    return tab, places, links

def species_level(r):
    """A real species (Genus species), not a genus, a family, sunlight or the decomposer community."""
    return bool(re.match(r'^[A-Z][a-z]+ [a-z]+$', r.get('latin') or '')) and not (r['latin'].endswith(' community') or r['latin'].endswith(' spp'))

def occurrences(tab, places):
    occ = {}
    for e in places:
        for n in e['nodes']:
            sp = n.get('sp')
            if sp and not n.get('cat') and sp in tab and tab[sp].get('wiki') and species_level(tab[sp]): occ.setdefault(sp, {})[e['id']] = (e['name'], e['lat'], e['lon'])
    return occ

def far_pair(ps):
    best = (0, None, None); v = list(ps.values())
    for i, a in enumerate(v):
        for b in v[i + 1:]:
            d = km(a[1], a[2], b[1], b[2])
            if d > best[0]: best = (d, a[0], b[0])
    return best

def covered(places, links):
    by = {e['id']: {n['id']: n.get('sp') for n in e['nodes']} for e in places}
    out = {}
    for j in links['cross']:
        for end in j.get('ends', []):
            sp = by.get(end.get('eco'), {}).get(end.get('node'))
            if sp: out.setdefault(sp, j.get('title') or j.get('id'))
    return out

def evidence(titles):
    """{wiki title: (score, snippet)}: 3 for a migrat* category, plus up to 2 for the word in the lead."""
    import wm
    out = {}
    for i in range(0, len(titles), 20):
        b = titles[i:i + 20]
        d = wm.get('https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=extracts|categories&exintro=1&explaintext=1&exlimit=20&cllimit=max&clshow=!hidden&titles=' + urllib.parse.quote('|'.join(b)))
        q = (d or {}).get('query', {}); redir = {}
        for k in ('normalized', 'redirects'):
            for r in q.get(k, []): redir[r['from']] = r['to']
        pages = {p['title']: p for p in q.get('pages', {}).values()}
        for t in b:
            y = t
            while y in redir and redir[y] != y: y = redir[y]
            p = pages.get(y) or {}
            text = p.get('extract') or ''; cats = ' '.join(c['title'] for c in p.get('categories', []))
            hits = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if re.search(r'migrat', s, re.I)]
            score = (3 if re.search(r'migrat', cats, re.I) else 0) + min(len(hits), 2)
            out[t] = (score, (hits[0][:220] if hits else ('category: ' + next((c['title'] for c in p.get('categories', []) if re.search('migrat', c['title'], re.I)), '')) if score else ''))
    return out

if __name__ == '__main__':
    tab, places, links = load(); occ = occurrences(tab, places); cov = covered(places, links)
    cand = []
    for sp, ps in occ.items():
        if len(ps) < 2: continue
        d, a, b = far_pair(ps)
        if d >= MIN_KM: cand.append(dict(sp=sp, name=tab[sp].get('name') or sp, wiki=tab[sp]['wiki'], n=len(ps), km=round(d), a=a, b=b))
    ev = {} if OFFLINE else evidence(sorted({c['wiki'] for c in cand}))
    for c in cand: c['score'], c['why'] = ev.get(c['wiki'], (0, ''))
    keep = [c for c in cand if c['score'] > 0] if not OFFLINE else cand
    keep.sort(key=lambda c: (-c['score'], -c['km'], -c['n']))
    out = ['# Journey candidates', '',
           '%d species live in places %d+ km apart; %d of them are described as migratory on Wikipedia%s. Top %d below. Score: 3 for a migration category plus up to 2 for the word in the article lead (max 5).' % (len(cand), MIN_KM, len(keep), ' (offline run: not checked)' if OFFLINE else '', TOP), '',
           '| # | Species | Score | Places | Farthest pair | Existing journey | Evidence |', '|---|---|---|---|---|---|---|']
    for i, c in enumerate(keep[:TOP], 1):
        out.append('| %d | %s (%s) | %s | %d | %s <-> %s, %d km | %s | %s |' % (i, c['name'], c['sp'], c['score'], c['n'], c['a'], c['b'], c['km'], cov.get(c['sp'], ''), c['why'].replace('|', '/')))
    os.makedirs(os.path.join(ROOT, 'research'), exist_ok=True)
    open(os.path.join(ROOT, 'research', 'journey-candidates.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out[:20]))
