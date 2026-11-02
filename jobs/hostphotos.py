#!/usr/bin/env python3
"""hostphotos.py: our own small copy of each species picture, with its author and licence.
Usage: hostphotos.py [place id | all] [limit]
For each Wikipedia title in photos/species.json (only the species of one place when a place id is given):
  1. reads author and licence from the Wikimedia Commons file page (50 files per request);
  2. skips the picture when the licence is unknown or not a free one (nothing is hosted without a credit we can show);
  3. downloads the 330 px thumbnail, shrinks it to 96 px WebP and writes photos/species/<id>.webp.
Writes photos/species_hosted.json {title: file name} and adds credits to photos/species_metadata.json. Resumable; polite pace via wm.py."""
import sys, os, io, re, json, hashlib, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm
OUT = 'photos/species'; HOSTED = 'photos/species_hosted.json'; META = 'photos/species_metadata.json'; SKIPPED = 'photos/species_hosted_skipped.json'
BASE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
# Free licences only. Added 2026-11 (#290): Copyrighted free use, No restrictions, Free Art Licence (FAL), KOGL Type 1, LGPL. Anything else stays unhosted.
FREE = re.compile(r'^(CC[ -]BY(?![ -]N[CD])|CC0|Public domain|PD|GFDL|Attribution|Copyrighted free use|No restrictions|FAL|Free Art Licen[cs]e|KOGL Type 1|LGPL)', re.I)
def retry(reason): return reason == 'no licence found' or bool(FREE.match(reason))   # skipped before for a reason a fix may have removed
def commons_file(u):
    """File name on Commons from a manifest path: relative 'a/ab/Name.jpg/330px-Name.jpg', or an absolute upload.wikimedia.org .../commons/ URL (full size or thumb). None for other wikis."""
    if not u.startswith('http'):
        parts = u.split('/'); return urllib.parse.unquote(parts[2]) if len(parts) >= 3 else None
    parts = u.split('/')
    if len(parts) < 8 or parts[2] != 'upload.wikimedia.org' or parts[3:5] != ['wikipedia', 'commons']: return None
    i = 7 if parts[5] != 'thumb' else 8
    return urllib.parse.unquote(parts[i]) if len(parts) > i else None
def thumb_path(u):
    """Path below BASE of the 330 px thumbnail."""
    if not u.startswith('http'): return u
    parts = u.split('/')[5:]
    if parts[0] == 'thumb': return '/'.join(parts[1:])
    return '%s/%s/%s/330px-%s' % (parts[0], parts[1], parts[2], parts[2])
def fid(title): return hashlib.sha1(title.encode()).hexdigest()[:12]
def load(p, d): return json.load(open(p)) if os.path.exists(p) else d
def strip(s): return re.sub(r'<[^>]+>', '', s or '').replace('&amp;', '&').strip()
def titles_for(place, man):
    if place in ('', 'all'): return sorted(man)
    sp = json.load(open('data/species/species.json')); d = json.load(open('data/%s.json' % place))
    wikis = {sp[n['sp']].get('wiki') for n in d['nodes'] if n.get('sp') in sp}
    return sorted(t for t in wikis if t in man)
def main():
    from PIL import Image   # imported here so the helpers above can be tested without Pillow
    place = sys.argv[1] if len(sys.argv) > 1 else 'all'; limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    man = json.load(open('photos/species.json')); hosted = load(HOSTED, {}); meta = load(META, {}); skipped = load(SKIPPED, {})
    todo = [t for t in titles_for(place, man) if t not in hosted and (t not in skipped or retry(skipped[t]))]
    if limit: todo = todo[:limit]
    print(len(todo), 'pictures to host', flush=True); os.makedirs(OUT, exist_ok=True)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; files = {}
        for t in batch:
            f = commons_file(man[t][0])
            if f: files[t] = f
            else: skipped[t] = 'not on Commons'
        q = 'https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json&titles=' + urllib.parse.quote('|'.join('File:' + f for f in files.values()))
        j = wm.get(q) or {}; info = {}
        for p in j.get('query', {}).get('pages', {}).values():
            em = (p.get('imageinfo') or [{}])[0].get('extmetadata', {})
            info[p.get('title', '')[5:].replace(' ', '_')] = em
        for t in batch:
            f = files.get(t); em = info.get((f or '').replace(' ', '_'))
            lic = strip((em or {}).get('LicenseShortName', {}).get('value'))
            if em:   # credits are recorded for every picture looked up, hosted or not
                meta[t] = {'a': strip(em.get('Artist', {}).get('value')) or 'Unknown', 'l': lic or 'unknown', 'lu': strip(em.get('LicenseUrl', {}).get('value')),
                           'p': 'https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(f)}
            if t not in files: continue   # not a Commons file: reason already recorded
            if not em or not FREE.match(lic): skipped[t] = lic or 'no licence found'; continue
            raw = wm.get(BASE + thumb_path(man[t][0]), raw=True)
            if not raw: skipped[t] = 'download failed'; continue
            try:
                im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((96, 96))
                name = fid(t) + '.webp'; im.save(os.path.join(OUT, name), 'WEBP', quality=72, method=6)
            except Exception as e:
                skipped[t] = 'bad image'; continue
            hosted[t] = name; skipped.pop(t, None)
        for p, d in ((HOSTED, hosted), (META, meta), (SKIPPED, skipped)): json.dump(d, open(p, 'w'), indent=0, sort_keys=True)
        print('done', min(i + 50, len(todo)), 'hosted', len(hosted), 'skipped', len(skipped), flush=True)
if __name__ == '__main__': main()
