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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https
import licences
from commons_api import ORIG, THUMB, NOTPHOTO, is_photo_type, open_licence, strip, image_names, manifest_entry, wikidata_images, resolve, commons_info   # moved unchanged to lib/commons_api.py
MAN = 'photos/species.json'; MISS = 'photos/species_missing.json'; SRC = 'photos/species_source.json'; TRIED = 'photos/species_commons_tried.json'
RETRY_DAYS = 90
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv   # --again: try the titles again even if tried lately (after a fix to the lookup)
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, src, tried = load(MAN), load(MISS), load(SRC), load(TRIED)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t not in man and (again or tried.get(t, '') <= cut))
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
