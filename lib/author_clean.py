"""author_clean.py: one rule for how a picture's author text is stored and shown (#887; owner, 15 Nov: "treat email as no author").

Commons gives the credit as free text. clean_author() turns it into the name or handle the licence needs, or '' when there is no usable author:
  - an email address is no author (privacy); "Name <a@b.c>" keeps the name
  - "The original uploader was X at English Wikipedia." -> X; "No machine-readable author provided. X assumed (based on copyright claims)." -> X
  - "X (talk) 06:06, 13 January 2009 (UTC)" -> X; camera / GPS boilerplate after "Camera location" is cut; web addresses are cut
  - html tags and entities are removed; "Unknown", "Anonymous", "Unknown authorUnknown author" and the like are '' (UNKNOWN)
A plain name or handle is returned unchanged. Pure text, no network: PlacePhotos.put() and the author rule in jobs/ both use it."""
import html, re

UNKNOWN = {'', 'unknown', 'unknown author', 'anonymous', 'author unknown', 'n/a', '?', 'see file page'}
_EMAIL = re.compile(r'<?[\w.+-]+@[\w-]+(?:\.[\w-]+)+>?')
_URL = re.compile(r'(?:https?://|www\.)\S+')

def _squash(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s or ''))).strip()

def is_unknown(a):
    a = (a or '').strip().lower()
    return a in UNKNOWN or a.startswith('unknown')

def clean_author(a):
    s = _squash(a)
    m = re.search(r'original uploader was (.+?) at (?:the )?(?:English )?(?:en\.)?wikipedia', s, re.I)
    if m: s = m.group(1)
    m = re.match(r'no machine-readable author provided\.? (.+?) assumed', s, re.I)
    if m: s = m.group(1)
    s = re.split(r'\s*\(talk\)', s, maxsplit=1, flags=re.I)[0]
    s = re.split(r'Camera location', s, maxsplit=1)[0]
    s = _EMAIL.sub('', s); s = _URL.sub('', s)
    s = re.sub(r'\s+', ' ', s).strip(' -–—:;,|/')
    return '' if is_unknown(s) else s

def is_dirty(a):
    """A stored author that clean_author would change (an unknown author is not dirty: it is a different case)."""
    return not is_unknown(a) and clean_author(a) != _squash(a)
