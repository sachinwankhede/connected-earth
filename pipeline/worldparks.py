#!/usr/bin/env python3
"""worldparks.py <countries|all> [divisor] [max]: candidate national parks outside the US, from Wikidata (with the English Wikipedia article for each).
countries: comma-separated English country names, or 'all' (every sovereign state except the US).
Quota per country = sqrt(land area in km2) / divisor (default 70), at least 3, at most max (default 40).
Rank = number of Wikipedia languages (a good stand-in for how well known a park is), plus a bonus for World Heritage sites.
Picking is greedy: the best-ranked park first, then parks 200 km or more from those already picked, then the rest, so a quota spreads over the country.
Parks under 5 km2 are dropped (forts, museums and city parks that Wikidata files as national parks).
Parks we already have (same Wikipedia article, same name, or a place within 5 km) are marked 'have'. Writes
pipeline/reports/worldparks.json (the list) and prints a markdown report. Only a list: no place files are made here."""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, os.path.join(ROOT, 'build')); import species
UA = 'ConnectedEarth/1.0 (https://github.com/sachinwankhede/connected-earth; data job)'
QC = '''SELECT ?c ?cLabel ?area WHERE {
  ?c wdt:P31 wd:Q3624078 ; wdt:P2046 ?area . FILTER NOT EXISTS { ?c wdt:P576 ?end }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}'''
Q = '''SELECT ?p ?pLabel ?coord ?area ?inc ?catLabel ?wh ?sl ?art WHERE {
  ?p wdt:P31/wdt:P279* wd:Q46169 ; wdt:P17 wd:%s ; wdt:P625 ?coord ; wikibase:sitelinks ?sl .
  ?art schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> .
  OPTIONAL { ?p p:P2046/psn:P2046/wikibase:quantityAmount ?area } OPTIONAL { ?p wdt:P571 ?inc } OPTIONAL { ?p wdt:P814 ?cat }
  OPTIONAL { ?p wdt:P1435 ?wh . FILTER(?wh = wd:Q9259) }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
} LIMIT 800'''
def sparql(q):
    for t in range(5):
        try:
            r = urllib.request.Request('https://query.wikidata.org/sparql?format=json&query=' + urllib.parse.quote(q), headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
            return json.load(urllib.request.urlopen(r, timeout=120))['results']['bindings']
        except Exception as ex:
            print('retry', t, ex, file=sys.stderr); time.sleep(10 * (t + 1))
    return None
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip()
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))
have_url, have_name, have_pt = set(), set(), []
for p in species.files():
    e = json.load(open(p))
    for s in e.get('sources', []): have_url.add(s.get('url', '').split('#')[0])
    have_name.add(norm(e.get('name', '')))
    if e.get('lat') is not None: have_pt.append((e['lat'], e['lon']))
def toks(s): return {w for w in norm(s).split() if w not in ('national', 'park', 'the', 'of', 'and', 'reserve', 'nature') and len(w) > 2}
have_toks = [x for x in (toks(n) for n in have_name) if x]
def ours(c):
    if c['art'] in have_url or norm(c['name']) in have_name: return True
    r = min(60, max(5, math.sqrt(c['area']) / 2)) if c.get('area') else 5   # a big park's point can sit far from ours
    if any(km(c['lat'], c['lon'], a, b) < r for a, b in have_pt): return True
    t = toks(c['name'])
    return bool(t) and any(len(t & h) / len(t | h) >= 0.6 for h in have_toks)
def pick(L, quota):
    got = []
    for c in sorted(L, key=lambda c: -c['score']):
        if len(got) < quota and all(km(c['lat'], c['lon'], g['lat'], g['lon']) >= 200 for g in got): got.append(c)
    for c in sorted(L, key=lambda c: -c['score']):
        if len(got) < quota and c not in got: got.append(c)
    return sorted(got, key=lambda c: -c['score'])
sel = sys.argv[1]; divisor = float(sys.argv[2]) if len(sys.argv) > 2 else 70; qmax = int(sys.argv[3]) if len(sys.argv) > 3 else 40
rows = sparql(QC)
if rows is None: sys.exit('Wikidata did not answer the country list')
cs = {}
for r in rows:
    name = r['cLabel']['value']
    if name in ('United States of America', 'United States') or re.match(r'^Q\d+$', name): continue
    cs[name] = (r['c']['value'].rsplit('/', 1)[1], float(r['area']['value']))   # land area in km2 (wdt: gives the value in the unit it was entered, km2)
want = sorted(cs) if sel.strip().lower() == 'all' else [x.strip() for x in sel.split(',') if x.strip()]
out = {}; lines = []; total = 0
for ct in want:
    if ct not in cs: lines.append('## %s\n\nNot found as a sovereign state on Wikidata.\n' % ct); continue
    qid, area = cs[ct]
    rows = sparql(Q % qid)
    if rows is None: print('FAILED', ct, file=sys.stderr); lines.append('## %s\n\nWikidata did not answer.\n' % ct); continue
    best = {}
    for r in rows:
        m = re.match(r'Point\(([-\d.eE+]+) ([-\d.eE+]+)\)', r['coord']['value'])
        if not m: continue
        k = r['p']['value']; label = r.get('pLabel', {}).get('value', '')
        if re.match(r'^Q\d+$', label): continue
        c = best.setdefault(k, dict(name=label, lon=float(m.group(1)), lat=float(m.group(2)), art=r['art']['value'].split('#')[0], sl=int(r['sl']['value']), wh=False, area=None, year=None, cat=None))
        if 'wh' in r: c['wh'] = True
        if 'area' in r and c['area'] is None: c['area'] = round(float(r['area']['value']) / 1e6)   # km2
        if 'inc' in r and c['year'] is None: c['year'] = r['inc']['value'][:4]
        if 'catLabel' in r and c['cat'] is None and not r['catLabel']['value'].startswith('http'): c['cat'] = r['catLabel']['value'].replace('IUCN category ', '').split(':')[0]
    L = [c for c in best.values() if c['area'] is None or c['area'] >= 5]
    for c in L: c['have'] = ours(c); c['score'] = c['sl'] + (15 if c['wh'] else 0)
    quota = int(min(qmax, max(3, round(math.sqrt(area) / divisor))))
    new = pick([c for c in L if not c['have']], quota)
    out[ct] = dict(land_km2=round(area), found=len(L), have=sum(c['have'] for c in L), quota=quota, new=new); total += len(new)
    lines.append('## %s: quota %d (land %d km2); %d national parks on Wikidata, %d already here, %d new listed\n' % (ct, quota, round(area), len(L), out[ct]['have'], len(new)))
    if new:
        lines.append('| Park | Year | km2 | IUCN | Languages | WH |\n|---|---|---|---|---|---|')
        for c in new: lines.append('| [%s](%s) | %s | %s | %s | %d | %s |' % (c['name'], c['art'], c['year'] or '', c['area'] or '', c['cat'] or '', c['sl'], 'yes' if c['wh'] else ''))
    lines.append('')
    print('%s: %d found, quota %d' % (ct, len(L), quota), file=sys.stderr); time.sleep(1.5)
os.makedirs(os.path.join(here, 'reports'), exist_ok=True)
json.dump(out, open(os.path.join(here, 'reports', 'worldparks.json'), 'w'), ensure_ascii=False, indent=1)
print('**%d countries, %d new parks listed.**\n\n' % (len(out), total) + '\n'.join(lines))
