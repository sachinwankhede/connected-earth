#!/usr/bin/env python3
"""worldparks.py <countries> [cap]: candidate national parks outside the US, from Wikidata (with the English Wikipedia article for each).
countries: comma-separated English country names.  cap: most parks listed per country (default 15), highest rank first.
Rank = number of Wikipedia languages (a good stand-in for how well known a park is), with World Heritage sites first.
Parks we already have (same Wikipedia article, same name, or a place within 5 km) are marked 'have'. Writes
pipeline/reports/worldparks.json (the list) and prints a markdown report. Only a list: no place files are made here."""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, os.path.join(ROOT, 'build')); import species
UA = 'ConnectedEarth/1.0 (https://github.com/sachinwankhede/connected-earth; data job)'
Q = '''SELECT ?p ?pLabel ?coord ?area ?inc ?cat ?catLabel ?wh ?sl ?art WHERE {
  ?c wdt:P31 wd:Q6256 ; rdfs:label "%s"@en .
  ?p wdt:P31/wdt:P279* wd:Q46169 ; wdt:P17 ?c ; wdt:P625 ?coord ; wikibase:sitelinks ?sl .
  ?art schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> .
  OPTIONAL { ?p wdt:P2046 ?area } OPTIONAL { ?p wdt:P571 ?inc } OPTIONAL { ?p wdt:P814 ?cat }
  OPTIONAL { ?p wdt:P1435 ?wh . FILTER(?wh = wd:Q9259) }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
} LIMIT 500'''
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
def ours(c):
    if c['art'] in have_url or norm(c['name']) in have_name: return True
    return any(km(c['lat'], c['lon'], a, b) < 5 for a, b in have_pt)
countries = [x.strip() for x in sys.argv[1].split(',') if x.strip()]; cap = int(sys.argv[2]) if len(sys.argv) > 2 else 15
out = {}; lines = []
for ct in countries:
    rows = sparql(Q % ct.replace('"', ''))
    if rows is None: print('FAILED', ct, file=sys.stderr); lines.append('## %s\n\nWikidata did not answer.\n' % ct); continue
    best = {}
    for r in rows:
        m = re.match(r'Point\(([-\d.eE+]+) ([-\d.eE+]+)\)', r['coord']['value'])
        if not m: continue
        k = r['p']['value']; label = r.get('pLabel', {}).get('value', '')
        if re.match(r'^Q\d+$', label): continue
        c = best.setdefault(k, dict(name=label, lon=float(m.group(1)), lat=float(m.group(2)), art=r['art']['value'].split('#')[0], sl=int(r['sl']['value']), wh=False, area=None, year=None, cat=None))
        if 'wh' in r: c['wh'] = True
        if 'area' in r and c['area'] is None: c['area'] = round(float(r['area']['value']))   # unit is whatever Wikidata holds (often km2); shown as is
        if 'inc' in r and c['year'] is None: c['year'] = r['inc']['value'][:4]
        if 'catLabel' in r and c['cat'] is None: c['cat'] = r['catLabel']['value']
    L = sorted(best.values(), key=lambda c: (not c['wh'], -c['sl']))
    for c in L: c['have'] = ours(c)
    new = [c for c in L if not c['have']][:cap]
    out[ct] = dict(found=len(L), have=sum(c['have'] for c in L), new=new)
    lines.append('## %s: %d national parks on Wikidata, %d already here, top %d new\n\n| Park | Year | Area | IUCN | Languages | WH |\n|---|---|---|---|---|---|' % (ct, len(L), out[ct]['have'], len(new)))
    for c in new: lines.append('| [%s](%s) | %s | %s | %s | %d | %s |' % (c['name'], c['art'], c['year'] or '', c['area'] or '', c['cat'] or '', c['sl'], 'yes' if c['wh'] else ''))
    lines.append('')
    print('%s: %d found' % (ct, len(L)), file=sys.stderr); time.sleep(2)
os.makedirs(os.path.join(here, 'reports'), exist_ok=True)
json.dump(out, open(os.path.join(here, 'reports', 'worldparks.json'), 'w'), ensure_ascii=False, indent=1)
print('\n'.join(lines))
