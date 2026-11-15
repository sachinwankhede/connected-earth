"""commons_api.py: Wikidata and Commons lookups for a picture (#421 B1; #887). MOVED unchanged from jobs/commonsphotos.py (which imports them back and keeps its species-picture job) so lib/place_sources.py
does not reach into jobs/. Network through lib/wm.py; licences by lib/licences.py."""
import os, re, json, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wm, licences
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https

ORIG = 'https://upload.wikimedia.org/wikipedia/commons/'
THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
NOTPHOTO = re.compile(r'logo|emblem|coat[_ ]of[_ ]arms|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|locator|diagram|[_ -]chart|distribution|range', re.I)
def is_photo_type(mime):
    """JPEG only: on Commons, PNG, GIF, SVG and TIFF files of a species are mostly maps, diagrams, drawings and scans (the first full run gave a gyre map for 'California Current')."""
    return (mime or '').lower() == 'image/jpeg'
def open_licence(lic): return licences.ok('Wikimedia', lic)   # the rule of #421, read from lib/allowed_sources.json
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
