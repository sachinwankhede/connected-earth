#!/usr/bin/env python3
"""openversephotos.py: a picture for species that Wikipedia, Wikidata, Commons and GBIF have none for (#511), from Openverse (api.openverse.org).
Usage: openversephotos.py [limit] [--again] [--dry]
For each title in photos/species_missing.json that has no manifest entry yet and is not a row marked abiotic (non_organisms):
  1. searches Openverse images for the Latin name (category photograph; licences CC0, public domain mark, CC BY, CC BY-SA; iNaturalist excluded);
  2. keeps a result only when the Latin name is in its title or tags (a free-text search is not a taxon match), it has a named creator, and it is not a
     herbarium sheet, museum object or iNaturalist photo (provider, source, title and links are all checked);
  3. downloads Openverse's OWN thumbnail (api.openverse.org/v1/images/<id>/thumb/), never the original host, and shrinks it to 96 px WebP in photos/species/<id>.webp.
A kept picture is written like a GBIF one: ['openverse/<id>', page] in photos/species.json, hosted in photos/species_hosted.json, creator, licence and the
Openverse page (openverse.org/image/<id>) in photos/species_metadata.json, source 'openverse' in photos/species_source.json; it leaves species_missing.json.
Titles with no usable picture get today's date in photos/species_openverse_tried.json and are tried again only after 90 days.
Stops at once and says so when Openverse answers 401 or 403 (a key is needed: that is a secret, ask the owner) or throttles three titles in a row.
--dry prints what would be kept and writes nothing. Only https links are fetched."""
import sys, os, re, json, hashlib, datetime, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm, gbifphotos as g
MAN, MISS, SRC = g.MAN, g.MISS, g.SRC; HOSTED, META, OUT = g.HOSTED, g.META, g.OUT
TRIED = 'photos/species_openverse_tried.json'
RETRY_DAYS = 90; TRY_FILES = 4
API = 'https://api.openverse.org/v1/images/'
# Openverse's licence codes -> (short name, licence link). Never NC or ND.
LICENCES = {('cc0', ''): ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'), ('pdm', ''): ('Public domain', 'https://creativecommons.org/publicdomain/mark/1.0'),
            ('by', None): ('CC BY', 'https://creativecommons.org/licenses/by/%s'), ('by-sa', None): ('CC BY-SA', 'https://creativecommons.org/licenses/by-sa/%s')}
BAD_PROVIDERS = ('inaturalist',)
def licence_of(r):
    """(short name with version, https licence link) for a result under CC0, PDM, CC BY or CC BY-SA, else None."""
    code = (r.get('license') or '').lower().strip(); ver = (r.get('license_version') or '').strip()
    if code in ('cc0', 'pdm'): name, link = LICENCES[(code, '')]; return (name, link)
    if code in ('by', 'by-sa') and re.fullmatch(r'\d\.\d', ver):
        name, link = LICENCES[(code, None)]; return ('%s %s' % (name, ver), link % ver)
    return None
def norm(s): return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).split())
def names_species(r, name):
    """True when the Latin name is in the title or one of the tags."""
    n = norm(name)
    return bool(n) and (n in norm(r.get('title')) or any(n in norm(t.get('name')) for t in r.get('tags') or []))
def unwanted(r):
    """True for iNaturalist (provider, source, or any link) and for herbarium or museum records."""
    blob = ' '.join(str(r.get(k) or '') for k in ('provider', 'source', 'foreign_landing_url', 'url', 'title', 'category', 'attribution')).lower()
    return any(b in blob for b in BAD_PROVIDERS) or any(w in blob for w in g.SHEET_WORDS) or 'herbarium' in blob
def candidates(results, name):
    """[(id, thumbnail link, creator, short licence, licence link)] in Openverse's order, only what may be used."""
    out = []
    for r in results or []:
        rid = r.get('id') or ''
        if not re.fullmatch(r'[0-9a-f-]{36}', rid) or unwanted(r) or not names_species(r, name): continue
        lic = licence_of(r); au = ' '.join(str(r.get('creator') or '').split())
        if not lic or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        th = API + rid + '/thumb/'
        out.append((rid, th, au, lic[0], lic[1]))
    return out
def non_organisms(root=None):
    """Wikipedia titles of the species rows marked abiotic (soils, lakes, water, nutrients: things in the food webs that are not living things); a search for such a title finds a photo of the thing the word names, not of a species (#511)."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = set(); base = os.path.join(root, 'data', 'species', 'rows')
    for d, _, fs in os.walk(base):
        for f in fs:
            if f.endswith('.json'):
                r = json.load(open(os.path.join(d, f), encoding='utf-8'))
                if r.get('cat') == 'abiotic' and r.get('wiki'): out.add(r['wiki'].replace('_', ' '))
    return out
def search(name):
    q = API + '?' + urllib.parse.urlencode({'q': '"%s"' % name, 'license': 'cc0,pdm,by,by-sa', 'category': 'photograph', 'excluded_source': 'inaturalist', 'page_size': 20})
    return (wm.get(q) or {}).get('results') or []
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv; dry = '--dry' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, src, tried, hosted, meta = load(MAN), load(MISS), load(SRC), load(TRIED), load(HOSTED), load(META)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    skip = non_organisms()
    todo = sorted(t for t in miss if t not in man and t.replace('_', ' ') not in skip and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); os.makedirs(OUT, exist_ok=True); found = 0; fails = 0
    def save():
        if dry: return
        for p, d in ((MAN, man), (MISS, miss), (SRC, src), (TRIED, tried), (HOSTED, hosted), (META, meta)):
            json.dump(d, open(p, 'w'), ensure_ascii=False, **({'indent': 0} if p in (HOSTED, META) else {'separators': (',', ':')}), sort_keys=(p in (SRC, TRIED, HOSTED, META)))
    for i, t in enumerate(todo, 1):
        name = t.replace('_', ' '); why = ''
        try:
            cs = candidates(search(name), name); why = '%d usable photos' % len(cs); fails = 0
            for rid, url, au, lic, lu in cs[:TRY_FILES]:
                webp = g.fetch_small(url)
                if not webp: why += '; %s too small or not an image' % rid; continue
                print('  yes:', t, '|', lic, '|', au, '| https://openverse.org/image/' + rid, flush=True)
                if dry: found += 1; why = ''; break
                f = g.fid(t) + '.webp'; open(os.path.join(OUT, f), 'wb').write(webp)
                man[t] = ['openverse/%s' % rid, urllib.parse.quote(t.replace(' ', '_'))]; hosted[t] = f; src[t] = 'openverse'
                meta[t] = {'a': au, 'l': lic, 'lu': lu, 'p': 'https://openverse.org/image/%s' % rid, 's': 'Openverse'}
                miss.pop(t, None); tried.pop(t, None); found += 1; why = ''; break
        except RuntimeError as e:
            fails += 1; print('  retry later:', t, '- request failed:', e, flush=True)
            if fails >= 3: print('STOP: three requests in a row failed (a key needed, or throttled); nothing more is tried. Ask the owner.', flush=True); save(); sys.exit(2)
            continue   # a failed request is not a "no picture": it is not remembered
        if t not in man: tried[t] = today.isoformat(); print('  no:', t, '-', why, flush=True)
        if i % 10 == 0 or i == len(todo): save(); print(i, 'of', len(todo), '| found', found, flush=True)
if __name__ == '__main__': main()
