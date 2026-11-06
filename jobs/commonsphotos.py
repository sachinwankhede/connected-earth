#!/usr/bin/env python3
"""commonsphotos.py: a picture for species that Wikipedia has none for (#421 part B1), from Wikidata and Wikimedia Commons.
Usage: commonsphotos.py [limit]
For each title in photos/species_missing.json that has no manifest entry yet:
  1. asks Wikidata for the item of that English Wikipedia page and reads its image property (P18), 50 titles per request;
  2. asks Commons for the file's licence, author and a 330 px thumbnail (50 files per request);
  3. keeps the picture only when the licence is CC0, CC BY, CC BY-SA or public domain (no non-commercial, no no-derivatives, no GFDL)
     and the file is a JPEG whose name does not say map, logo or diagram.
A kept picture is added to photos/species.json in the same shape speciesphotos.py writes, removed from species_missing.json and noted
in photos/species_source.json {title: 'wikidata-p18'}; hostphotos.py then downloads it and records author and licence as for any other picture.
Titles with no usable picture stay in species_missing.json (a plain 'nophoto', as its schema says) and get today's date in photos/species_commons_tried.json, so they are tried again only after 90 days. Resumable; polite pace via wm.py."""
import sys, os, re, json, datetime, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https
MAN = 'photos/species.json'; MISS = 'photos/species_missing.json'; SRC = 'photos/species_source.json'; TRIED = 'photos/species_commons_tried.json'
RETRY_DAYS = 90
ORIG = 'https://upload.wikimedia.org/wikipedia/commons/'
THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
# The open licences allowed for every source (#421): CC0, CC BY, CC BY-SA, public domain. Never NC, ND or GFDL.
OPEN = re.compile(r'^(CC0|CC[ -]BY([ -]SA)?([ -]\d[\d.]*)?( [A-Za-z]{2,3})?|Public domain|PD)\b', re.I)
CLOSED = re.compile(r'(^|[ -])(NC|ND)([ -]|$)', re.I)
NOTPHOTO = re.compile(r'logo|emblem|coat[_ ]of[_ ]arms|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|locator|diagram|[_ -]chart|distribution|range', re.I)
def is_photo_type(mime):
    """JPEG only: on Commons, PNG, GIF, SVG and TIFF files of a species are mostly maps, diagrams, drawings and scans (the first full run gave a gyre map for 'California Current')."""
    return (mime or '').lower() == 'image/jpeg'
def open_licence(lic): return bool(lic) and bool(OPEN.match(lic.strip())) and not CLOSED.search(lic)
def strip(s): return re.sub(r'<[^>]+>', '', s or '').replace('&amp;', '&').strip()
def image_names(claims):
    """File names of the P18 claims, preferred rank first, deprecated ones dropped."""
    rank = {'preferred': 0, 'normal': 1}; out = []
    for c in sorted(claims or [], key=lambda c: rank.get(c.get('rank'), 2)):
        if c.get('rank') == 'deprecated': continue
        v = (c.get('mainsnak') or {}).get('datavalue', {}).get('value')
        if isinstance(v, str) and not NOTPHOTO.search(v): out.append(v)
    return out
def manifest_entry(thumburl, title):
    """[path below the thumb folder, Wikipedia page name], as speciesphotos.py writes it (the full Commons link for an original too small to have a thumbnail); None for any other link."""
    u = (thumburl or '').split('?')[0]
    if not safe_https(u, ALLOWED_IMAGE_HOSTS): return None
    page = urllib.parse.quote(title.replace(' ', '_'))
    for th in (THUMB, THUMB.replace('upload.', 'thumb.')):   # Commons answers with thumb.wikimedia.org; speciesphotos.py stores the part after it
        if u.startswith(th): return [u[len(th):], page]
    if u.startswith(ORIG): return [u, page]   # an original smaller than 330 px has no thumbnail: the full link, which hostphotos.py downloads as it is
    return None
def wikidata_images(titles):
    """{title: [file names]} for the titles that have a Wikidata item with P18."""
    q = ('https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&props=claims%7Csitelinks&sitefilter=enwiki&format=json&titles='
         + urllib.parse.quote('|'.join(titles)))
    j = wm.get(q) or {}; out = {}
    if 'error' in j: raise RuntimeError('Wikidata said: ' + json.dumps(j['error'])[:300])
    for e in (j.get('entities') or {}).values():
        t = ((e.get('sitelinks') or {}).get('enwiki') or {}).get('title')
        if t: out[t] = image_names((e.get('claims') or {}).get('P18'))
    return out
def resolve(titles):
    """{title: the page it redirects to (or itself)} for up to 50 English Wikipedia titles: Wikidata knows only the real page title (#511)."""
    q = 'https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&titles=' + urllib.parse.quote('|'.join(titles))
    j = wm.get(q) or {}; qq = j.get('query') or {}; out = {t: t for t in titles}
    for k in ('normalized', 'redirects'):
        for r in qq.get(k, []):
            for t, v in list(out.items()):
                if v == r.get('from'): out[t] = r.get('to')
    return out
def commons_info(files):
    """{file name with underscores: (licence, author, licence url, thumbnail url, mime)} for up to 50 Commons files."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata%7Curl%7Cmime&iiurlwidth=330&format=json&titles='
         + urllib.parse.quote('|'.join('File:' + f for f in files)))
    j = wm.get(q) or {}; out = {}
    for p in (j.get('query') or {}).get('pages', {}).values():
        ii = (p.get('imageinfo') or [{}])[0]; em = ii.get('extmetadata', {})
        out[p.get('title', '')[5:].replace(' ', '_')] = (strip(em.get('LicenseShortName', {}).get('value')), strip(em.get('Artist', {}).get('value')),
                                                         strip(em.get('LicenseUrl', {}).get('value')), ii.get('thumburl', ''), ii.get('mime', ''))
    return out
def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, src, tried = load(MAN), load(MISS), load(SRC), load(TRIED)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t not in man and tried.get(t, '') <= cut)
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); found = 0; why = {}
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; res = resolve([t.replace('_', ' ') for t in batch]); names = wikidata_images(sorted(set(res.values())))
        files = sorted({n.replace(' ', '_') for v in names.values() for n in v[:2]})
        info = commons_info(files) if files else {}
        for t in batch:
            entry = None; k = res.get(t.replace('_', ' '), t.replace('_', ' '))
            if k not in names: why[t] = 'no Wikidata item for this page (after following redirects)'
            elif not names[k]: why[t] = 'item has no usable P18'
            for n in names.get(k, [])[:2]:
                lic, author, lu, thumb, mime = info.get(n.replace(' ', '_'), ('', '', '', '', ''))
                why[t] = 'file %s: licence %r, type %r, link %s' % (n, lic, mime, thumb[:220] or 'none')
                if is_photo_type(mime) and open_licence(lic):
                    entry = manifest_entry(thumb, t)
                    if entry: break
            if entry:
                man[t] = entry; miss.pop(t, None); tried.pop(t, None); src[t] = 'wikidata-p18'; found += 1
            else:
                tried[t] = today.isoformat()
        for p, d in ((MAN, man), (MISS, miss), (SRC, src), (TRIED, tried)): json.dump(d, open(p, 'w'), ensure_ascii=False, separators=(',', ':'), sort_keys=(p in (SRC, TRIED)))
        print(min(i + 50, len(todo)), 'of', len(todo), '| found', found, flush=True)
        for t in batch:
            if t not in man: print('  no:', t, '-', why.get(t, '?'), flush=True)
if __name__ == '__main__': main()
