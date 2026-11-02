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
from PIL import Image
OUT = 'photos/species'; HOSTED = 'photos/species_hosted.json'; META = 'photos/species_metadata.json'; SKIPPED = 'photos/species_hosted_skipped.json'
BASE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
FREE = re.compile(r'^(CC[ -]BY|CC0|Public domain|PD|GFDL|Attribution)', re.I)
def fid(title): return hashlib.sha1(title.encode()).hexdigest()[:12]
def load(p, d): return json.load(open(p)) if os.path.exists(p) else d
def strip(s): return re.sub(r'<[^>]+>', '', s or '').replace('&amp;', '&').strip()
def titles_for(place, man):
    if place in ('', 'all'): return sorted(man)
    sp = json.load(open('data/species.json')); d = json.load(open('data/%s.json' % place))
    wikis = {sp[n['sp']].get('wiki') for n in d['nodes'] if n.get('sp') in sp}
    return sorted(t for t in wikis if t in man)
def main():
    place = sys.argv[1] if len(sys.argv) > 1 else 'all'; limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    man = json.load(open('photos/species.json')); hosted = load(HOSTED, {}); meta = load(META, {}); skipped = load(SKIPPED, {})
    todo = [t for t in titles_for(place, man) if t not in hosted and t not in skipped]
    if limit: todo = todo[:limit]
    print(len(todo), 'pictures to host', flush=True); os.makedirs(OUT, exist_ok=True)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; files = {}
        for t in batch:
            parts = man[t][0].split('/')
            if len(parts) >= 3: files[t] = urllib.parse.unquote(parts[2])
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
            if not em or not FREE.match(lic): skipped[t] = lic or 'no licence found'; continue
            raw = wm.get(BASE + man[t][0], raw=True)
            if not raw: skipped[t] = 'download failed'; continue
            try:
                im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((96, 96))
                name = fid(t) + '.webp'; im.save(os.path.join(OUT, name), 'WEBP', quality=72, method=6)
            except Exception as e:
                skipped[t] = 'bad image'; continue
            hosted[t] = name
        for p, d in ((HOSTED, hosted), (META, meta), (SKIPPED, skipped)): json.dump(d, open(p, 'w'), indent=0, sort_keys=True)
        print('done', min(i + 50, len(todo)), 'hosted', len(hosted), 'skipped', len(skipped), flush=True)
if __name__ == '__main__': main()
