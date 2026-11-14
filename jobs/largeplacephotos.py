#!/usr/bin/env python3
"""largeplacephotos.py: a larger copy (400 px WebP) of each place picture, for the full-width hero on the place page (#727, owner 14 Nov).
Usage: largeplacephotos.py [most new copies in this run, default 30; 0 = no limit]
For each picture in photos/places/places.json that has no copy yet (photos/places_large.json, keyed by the same imgwiki title): downloads the Commons thumbnail of its file at 500 px (the 330 px one
when the original is smaller), shrinks it to at most 400 px and writes photos/places-lg/<same name as the small file, .webp>. Credit and licence are the existing ones in places.json; nothing new is credited.
Every download goes through wm.get (lib/fetch.py), which refuses unlisted hosts (upload.wikimedia.org is listed). Resumable and sorted by title, so a later run with a larger number adds more."""
import sys, os, io, json, hashlib, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
BASE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
OUT = 'photos/places-lg'; LARGE = 'photos/places_large.json'; PLACES = 'photos/places/places.json'; SIZE = 400; QUALITY = 70

def commons_name(page):
    """File name (underscores) from a Commons file page address, or None for any other address."""
    if not page or 'commons.wikimedia.org/wiki/File:' not in page: return None
    n = urllib.parse.unquote(page.split('File:', 1)[1].split('#')[0].split('?')[0]).replace(' ', '_')
    return n or None

def thumb_url(name, width):
    """Thumbnail address of a Commons file at width px (Commons serves 330, 500, 960 ...). The folder is the first characters of the md5 of the name."""
    h = hashlib.md5(name.encode()).hexdigest(); q = urllib.parse.quote(name)
    return '%s%s/%s/%s/%dpx-%s' % (BASE, h[0], h[:2], q, width, q)

def source_urls(page):
    n = commons_name(page)
    return [thumb_url(n, 500), thumb_url(n, 330)] if n else []

def download(urls, get):
    """Bytes of the first address that downloads, or None. A thumbnail that Commons cannot make (a TIFF or a very large original answers HTTP 400) is skipped, not fatal: that place keeps its small picture (#727)."""
    for u in urls:
        try: raw = get(u, raw=True)
        except RuntimeError as e: print('skipped', u[-70:], '-', e, flush=True); continue
        if raw: return raw
    return None

def out_name(f): return os.path.splitext(f)[0] + '.webp'

def shrink(im, size=SIZE):
    """(WebP bytes, (w, h)) of a copy of im at most size px on its longer side."""
    im = im.copy(); im.thumbnail((size, size)); buf = io.BytesIO(); im.save(buf, 'WEBP', quality=QUALITY, method=6)
    return buf.getvalue(), im.size

def todo(places, large, limit):
    """Titles still to do, sorted, at most limit (0 = all): a stored small file, an address on Commons and no copy yet."""
    t = [k for k in sorted(places) if places[k].get('f') and k not in large and commons_name(places[k].get('p'))]
    return t[:limit] if limit else t

def main():
    from PIL import Image
    import wm
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    places = json.load(open(PLACES)); large = json.load(open(LARGE)) if os.path.exists(LARGE) else {}
    work = todo(places, large, limit)
    print(len(places), 'pictures,', len(large), 'with a copy,', len(work), 'to do in this run', flush=True)
    os.makedirs(OUT, exist_ok=True); total = 0; biggest = 0
    for i, t in enumerate(work, 1):
        raw = download(source_urls(places[t]['p']), wm.get)
        if not raw: print('no download for', t, flush=True); continue
        try:
            data, size = shrink(Image.open(io.BytesIO(raw)).convert('RGB'))
        except Exception: print('bad image for', t, flush=True); continue
        name = out_name(places[t]['f']); open(os.path.join(OUT, name), 'wb').write(data); large[t] = name; total += len(data); biggest = max(biggest, len(data))
        print('%3d %-40s %3dx%-3d %5d KB' % (i, t[:40], size[0], size[1], round(len(data) / 1024)), flush=True)
        if i % 10 == 0: json.dump(large, open(LARGE, 'w'), indent=0, sort_keys=True)
    json.dump(large, open(LARGE, 'w'), indent=0, sort_keys=True)
    print('copies:', len(large), '; this run', round(total / 1024), 'KB, largest', round(biggest / 1024), 'KB', flush=True)

if __name__ == '__main__': main()
