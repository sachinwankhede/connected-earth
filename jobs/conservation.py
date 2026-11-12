#!/usr/bin/env python3
"""conservation.py [batch size, default 150] [limit of names, default all]: the conservation status of each species, from Wikidata (#680).
Wikidata states a species' conservation status (property P141) as a CC0 statement, using the IUCN category items. For each species in the table (by its Latin
name, property P225) this keeps the one best-ranked value and stores a short code: LC, NT, VU, EN, CR, EW, EX (DD, data deficient, is not stored: there is no
status to show). A species with no value, or with two different best-ranked values, gets no entry. Writes data/species/conservation.json
{lowercase Latin name: {"c": code, "q": Wikidata item}} and prints how many species were found. Only query.wikidata.org is asked (an allowed host, Wikimedia
CC0); nothing is taken from IUCN itself. Resumable: names already in the file are not asked again unless --again."""
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); import fetch
sys.path.insert(0, os.path.join(ROOT, 'build')); import species
OUT = os.path.join(ROOT, 'data/species/conservation.json'); ASKED = os.path.join(ROOT, 'data/species/conservation_asked.json')
UA = 'ConnectedEarth/1.0 (https://github.com/sachinwankhede/connected-earth; data job)'
CODES = {'Q211005': 'LC', 'Q719675': 'NT', 'Q278113': 'VU', 'Q11394': 'EN', 'Q96377276': 'EN', 'Q219127': 'CR', 'Q239509': 'EW', 'Q237350': 'EX'}   # Wikidata items for the IUCN categories (EN is both Q11394 and, as 'Endangered status', Q96377276: 117 species use the latter, found by the unmapped report)

def query(names):
    """SPARQL asking the best-ranked conservation status of every taxon with one of these names."""
    vals = ' '.join('"%s"' % n.replace('\\', '').replace('"', '') for n in names)
    return 'SELECT ?n ?i ?s WHERE { VALUES ?n { %s } ?i wdt:P225 ?n ; wdt:P141 ?s . }' % vals

def parse(rows, unknown=None):
    """{name: {"c": code, "q": item}} from SPARQL bindings: unknown categories (DD and others) are dropped, and a name whose items give different codes is dropped."""
    seen = {}
    for r in rows:
        name = r['n']['value']; item = r['i']['value'].rsplit('/', 1)[-1]; code = CODES.get(r['s']['value'].rsplit('/', 1)[-1])
        if code: seen.setdefault(name.lower(), set()).add((code, item))
        elif unknown is not None: unknown[r['s']['value'].rsplit('/', 1)[-1]] += 1   # #680: which status items are not mapped (an IUCN category missing from CODES shows up here)
    out = {}
    for name, vals in seen.items():
        if len({c for c, _ in vals}) == 1: c, q = sorted(vals)[0]; out[name] = {'c': c, 'q': q}
    return out

def sparql(q):
    for t in range(5):
        try:
            r = urllib.request.Request('https://query.wikidata.org/sparql?format=json&query=' + urllib.parse.quote(q), headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
            return json.load(fetch.urlopen(r, timeout=120))['results']['bindings']
        except Exception as ex:
            print('retry', t, ex, file=sys.stderr); time.sleep(10 * (t + 1))
    return None

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    size = int(args[0]) if args else 150; limit = int(args[1]) if len(args) > 1 else 0
    from collections import Counter; unknown = Counter()
    have = json.load(open(OUT)) if os.path.exists(OUT) and not again else {}
    asked = set(have) | set(json.load(open(ASKED)) if os.path.exists(ASKED) and not again else [])
    names = [r.get('latin') or r['name'] for r in species.table().values()]
    todo = [n for n in names if n.lower() not in asked]
    if limit: todo = todo[:limit]
    for i in range(0, len(todo), size):
        batch = todo[i:i + size]; rows = sparql(query(batch))
        if rows is None: print('batch failed, stopping', file=sys.stderr); break
        have.update(parse(rows, unknown)); asked.update(n.lower() for n in batch)
        time.sleep(2)
    json.dump(dict(sorted(have.items())), open(OUT, 'w'), indent=1, ensure_ascii=False)
    json.dump(sorted(asked - set(have)), open(ASKED, 'w'))
    print('asked %d names, %d have a status (%.0f%%)' % (len(asked), len(have), 100.0 * len(have) / max(1, len(asked))))
    print(dict(Counter(v['c'] for v in have.values())))
    print('unmapped status items (Wikidata id: count):', dict(unknown.most_common(15)))
