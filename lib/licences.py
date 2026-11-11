"""lib/licences.py: the picture licence rule (#421), read from lib/allowed_sources.json.
canonical(text) maps a licence as written on Commons or GBIF to one of CC0, CC BY, CC BY-SA, Public domain (None for anything else, never NC, ND, GFDL, LGPL, FAL, KOGL or vague tags).
ok(source, text) is true when the canonical name is in that source's allowed_licences."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'lib', 'allowed_sources.json')
_CC = re.compile(r'^CC[ -]BY(?:[ -](SA))?(?:[ -]\d[\d.]*)?(?: [A-Za-z]{2,3})?$', re.I)
_NO = re.compile(r'(^|[ -])(NC|ND)([ -]|$)', re.I)
def canonical(text):
    t = (text or '').strip()
    if not t or _NO.search(t): return None
    if re.match(r'^CC0([ -]\d[\d.]*)?$', t, re.I): return 'CC0'
    if re.match(r'^(Public domain|PD)$', t, re.I): return 'Public domain'
    m = _CC.match(t)
    if m: return 'CC BY-SA' if m.group(1) else 'CC BY'
    return None
def allowed(source):
    with open(PATH, encoding='utf-8') as f: return list(json.load(f)['sources'][source]['allowed_licences'])
def ok(source, text):
    c = canonical(text)
    return c is not None and c in allowed(source)
class _Matcher:
    def __init__(self, source): self.source = source
    def match(self, text): return ok(self.source, text)
def matcher(source):
    """An object with .match(text) that is true for an allowed licence, for code that used a regex."""
    return _Matcher(source)
