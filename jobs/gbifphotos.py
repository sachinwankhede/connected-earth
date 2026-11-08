#!/usr/bin/env python3
"""gbifphotos.py: a picture for species that Wikipedia, Wikidata and Commons have none for (#421 part B2, #511), from GBIF occurrence media.
Usage: gbifphotos.py [limit] [--again]
For each title in photos/species_missing.json that has no manifest entry yet:
  1. asks GBIF to match the name (species/match), and keeps only an EXACT match;
  2. asks for observation photos of that taxon (occurrence/search with mediaType StillImage, licence CC0 or CC BY only);
  3. drops every record that comes from iNaturalist (its dataset, institution code or links) and every herbarium or museum specimen sheet
     (only human or machine observations and living specimens are used), and every photo without a named author;
  4. downloads the first picture that decodes and is at least 200 px on its short side, shrinks it to 96 px WebP in photos/species/<id>.webp.
A kept picture is written like a Commons one: an entry in photos/species.json ['gbif/<occurrence>', page], hosted in photos/species_hosted.json, its author,
licence and the GBIF occurrence page in photos/species_metadata.json, the source 'gbif' in photos/species_source.json; it leaves species_missing.json.
Titles with no usable picture stay in species_missing.json and get today's date in photos/species_gbif_tried.json, so they are tried again only after 90 days.
Resumable, polite pace via wm.py. Only https links are fetched; nothing is stored but the 96 px copy and its credit."""
import sys, os, io, re, json, hashlib, datetime, ipaddress, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm
MAN = 'photos/species.json'; MISS = 'photos/species_missing.json'; SRC = 'photos/species_source.json'; TRIED = 'photos/species_gbif_tried.json'
HOSTED = 'photos/species_hosted.json'; META = 'photos/species_metadata.json'; OUT = 'photos/species'
RETRY_DAYS = 90; MIN_SIDE = 200; MAX_BYTES = 12_000_000; TRY_FILES = 4
API = 'https://api.gbif.org/v1/'
INAT_DATASET = '50c9509d-22c7-4a22-a47d-8c48425ef4a7'
# the only licences kept (GBIF's own spelling): CC0 and CC BY. Never NC, ND or SA-only.
LICENCES = {'http://creativecommons.org/publicdomain/zero/1.0/': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'),
            'http://creativecommons.org/licenses/by/4.0/': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'),
            'http://creativecommons.org/licenses/by/3.0/': ('CC BY 3.0', 'https://creativecommons.org/licenses/by/3.0')}
BASIS_OK = {'HUMAN_OBSERVATION', 'MACHINE_OBSERVATION', 'LIVING_SPECIMEN', 'OBSERVATION'}
def licence_of(media):
    """(short name, https licence link) for a media record under CC0 or CC BY, else None. GBIF gives the licence as a link or as its enum name."""
    v = (media.get('license') or '').strip()
    if not v: return None
    v = {'CC0_1_0': 'http://creativecommons.org/publicdomain/zero/1.0/', 'CC_BY_4_0': 'http://creativecommons.org/licenses/by/4.0/'}.get(v, v)
    if not v.endswith('/'): v += '/'
    v = v.replace('https://', 'http://', 1)
    return LICENCES.get(v)
def from_inaturalist(rec, media):
    """True for a record that came through iNaturalist: its dataset, institution code, or any link of the record."""
    blob = ' '.join(str(x) for x in (rec.get('institutionCode'), rec.get('collectionCode'), rec.get('references'), media.get('references'), media.get('identifier'), media.get('source'), media.get('publisher')) if x).lower()
    return rec.get('datasetKey') == INAT_DATASET or 'inaturalist' in blob
def safe_url(u):
    """https only, a named host (no address, no localhost), no credentials in the link."""
    try: p = urllib.parse.urlsplit(u or '')
    except ValueError: return False
    if p.scheme != 'https' or not p.hostname or p.username or p.password: return False
    h = p.hostname.lower()
    if h == 'localhost' or h.endswith('.local') or '.' not in h: return False
    try: ipaddress.ip_address(h); return False
    except ValueError: return True
def author_of(rec, media):
    a = ' '.join(str(media.get('creator') or media.get('rightsHolder') or rec.get('recordedBy') or '').split())
    return a if a and a.lower() not in ('unknown', 'anonymous', 'n/a', 'none') else ''
def candidates(results):
    """[(occurrence key, picture link, author, short licence, licence link)] from occurrence/search results, best first (the order GBIF gave), only what may be used."""
    out = []
    for rec in results or []:
        if rec.get('basisOfRecord') not in BASIS_OK or not rec.get('key'): continue
        for m in rec.get('media') or []:
            if m.get('type') != 'StillImage' or not safe_url(m.get('identifier')): continue
            lic = licence_of(m); au = author_of(rec, m)
            if not lic or not au or from_inaturalist(rec, m): continue
            out.append((rec['key'], m['identifier'], au, lic[0], lic[1])); break   # one picture per occurrence
    return out
def match(name):
    """The GBIF taxon key when the name matches exactly (species or genus, accepted or synonym), else None."""
    j = wm.get(API + 'species/match?verbose=false&name=' + urllib.parse.quote(name)) or {}
    if j.get('matchType') != 'EXACT' or not j.get('usageKey'): return None
    return j['usageKey']
def search(key):
    q = (API + 'occurrence/search?mediaType=StillImage&occurrenceStatus=PRESENT&license=CC0_1_0&license=CC_BY_4_0&limit=40&taxonKey=%s' % key
         + ''.join('&basisOfRecord=' + b for b in sorted(BASIS_OK)))
    return (wm.get(q) or {}).get('results') or []
def fid(title): return hashlib.sha1(title.encode()).hexdigest()[:12]
def fetch_small(url):
    """The picture as a 96 px WebP (bytes), or None when it is too big, not an image, or under 200 px on its short side."""
    from PIL import Image
    raw = wm.get(url, raw=True, tries=2)
    if not raw or len(raw) > MAX_BYTES: return None
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
        if min(im.size) < MIN_SIDE: return None
        im = im.convert('RGB'); im.thumbnail((96, 96)); b = io.BytesIO(); im.save(b, 'WEBP', quality=72, method=6); return b.getvalue()
    except Exception: return None
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, src, tried, hosted, meta = load(MAN), load(MISS), load(SRC), load(TRIED), load(HOSTED), load(META)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t not in man and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); os.makedirs(OUT, exist_ok=True); found = 0
    def save():
        for p, d in ((MAN, man), (MISS, miss), (SRC, src), (TRIED, tried), (HOSTED, hosted), (META, meta)):
            json.dump(d, open(p, 'w'), ensure_ascii=False, **({'indent': 0} if p in (HOSTED, META) else {'separators': (',', ':')}), sort_keys=(p in (SRC, TRIED, HOSTED, META)))
    for i, t in enumerate(todo, 1):
        name = t.replace('_', ' '); why = ''
        try:
            key = match(name)
            if not key: why = 'no exact GBIF match'
            else:
                cs = candidates(search(key)); why = '%d usable photos' % len(cs)
                for ok, url, au, lic, lu in cs[:TRY_FILES]:
                    webp = fetch_small(url)
                    if not webp: why += '; %s too small or not an image' % ok; continue
                    f = fid(t) + '.webp'; open(os.path.join(OUT, f), 'wb').write(webp)
                    man[t] = ['gbif/%s' % ok, urllib.parse.quote(t.replace(' ', '_'))]; hosted[t] = f; src[t] = 'gbif'
                    meta[t] = {'a': au, 'l': lic, 'lu': lu, 'p': 'https://www.gbif.org/occurrence/%s' % ok}
                    miss.pop(t, None); tried.pop(t, None); found += 1; why = ''; break
        except RuntimeError as e: print('  retry later:', t, '- request failed:', e, flush=True); continue   # a failed request is not a "no picture": it is not remembered
        if t not in man: tried[t] = today.isoformat(); print('  no:', t, '-', why, flush=True)
        if i % 10 == 0 or i == len(todo): save(); print(i, 'of', len(todo), '| found', found, flush=True)
if __name__ == '__main__': main()
