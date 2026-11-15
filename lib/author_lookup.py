"""author_lookup.py: ask Commons who made a picture (#887). The rules of jobs/authorlookup.py (the read-only report) and of jobs/placepictures.py, in lib/ so lib/place_sources.py does not reach into jobs/.
MOVED unchanged from jobs/authorlookup.py, which imports them back. Network through lib/wm.py (commons.wikimedia.org is already allowed); the stored form of an author is lib/author_clean.py."""
import json, os, re, sys, urllib.parse, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wm, author_clean

API = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo|revisions&iiprop=extmetadata&iiextmetadatafilter=Artist|Credit|Attribution' \
      '&rvprop=user&rvdir=newer&rvlimit=1&titles='
UNKNOWN = {'', 'unknown', 'unknown author', 'anonymous', 'author unknown', 'n/a', '?', 'see file page'}
def strip(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s or ''))).strip()
def unknown(author):
    """No usable author: empty, 'Unknown ...', or only an email address (lib/author_clean.py)."""
    return author_clean.clean_author(author) == ''
def clean(author):
    return author_clean.clean_author(author)
def by_licence(lic):
    return (lic or '').upper().startswith('CC BY')
def file_of(page_url):
    """The Commons file name from a credit-page address, or ''."""
    return urllib.parse.unquote((page_url or '').split('File:')[-1]) if 'File:' in (page_url or '') else ''
def classify(meta, uploader):
    """(class, name) from the Commons extmetadata dict and the first revision's user."""
    v = lambda k: strip((meta.get(k) or {}).get('value'))
    if v('Artist') and not unknown(v('Artist')): return 'artist', v('Artist')
    if v('Attribution') and not unknown(v('Attribution')): return 'attribution', v('Attribution')
    if 'own work' in v('Credit').lower() and uploader: return 'own-work', uploader
    return 'none', ''
def lookup(fn):
    j = wm.get(API + urllib.parse.quote('File:' + fn)) or {}
    page = next(iter(((j.get('query') or {}).get('pages') or {}).values()), {})
    meta = ((page.get('imageinfo') or [{}])[0]).get('extmetadata') or {}
    uploader = ((page.get('revisions') or [{}])[0]).get('user') or ''
    return classify(meta, uploader)
