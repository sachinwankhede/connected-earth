#!/usr/bin/env python3
"""largephotos.py: a larger copy (400 px WebP) of the picture of the species people open most (#421 part A).
Usage: largephotos.py [how many of the most-used species, default 30]
The ranking is the number of places a species is in (every place, main and pilot), most first, then by name; only species that already have a hosted picture
(photos/species_hosted.json) take part, so the credit and licence are the ones already in photos/species_metadata.json and nothing new needs crediting.
For each one not yet done: downloads the 500 px thumbnail from Commons (a standard size; the 330 px one when the original is smaller), shrinks it to at most 400 px
and writes photos/species-lg/<same file name as the thumbnail>. Writes photos/species_large.json {title: file name}. Resumable; polite pace via wm.py."""
import sys, os, io, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'build'))
import wm, hostphotos as hp
OUT = 'photos/species-lg'; LARGE = 'photos/species_large.json'; SIZE = 400; QUALITY = 70

def width_path(u, w):
    """Path below hp.BASE of the thumbnail of the manifest picture u at w px wide (Commons serves 330, 500, 960 ... only)."""
    p = hp.thumb_path(u).split('/')
    p[-1] = re.sub(r'^\d+px-', '%dpx-' % w, p[-1])
    return '/'.join(p)

def ranking(ecos, hosted):
    """[(title, number of places)] most places first: one entry per species, under the same title the species page takes its picture from (the Latin name first, then its Wikipedia titles)."""
    where, keys = {}, {}
    for e in ecos:
        for n in e['nodes']:
            if n.get('cat') or not n.get('latin'): continue
            l = n['latin'].lower(); where.setdefault(l, set()).add(e['id'])
            keys.setdefault(l, set()).update(k for k in (n['latin'], n.get('wiki'), n.get('canonicalWiki')) if k)
    out, seen = [], set()
    for l in where:
        t = next((k for k in sorted(keys[l], key=lambda k: (k.lower() != l, k)) if k in hosted), None)
        if t and t not in seen: seen.add(t); out.append((-len(where[l]), t))
    return [(t, -c) for c, t in sorted(out)]

def main():
    from PIL import Image
    import build
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    hosted = hp.load(hp.HOSTED, {}); man = json.load(open('photos/species.json')); large = hp.load(LARGE, {})
    rank = ranking(build.load_places(True)[1], hosted)[:top]
    todo = [(t, c) for t, c in rank if t not in large and t in man]
    print(len(rank), 'in the ranking,', len(todo), 'to do; the first ten:', ', '.join('%s (%d)' % x for x in rank[:10]), flush=True)
    os.makedirs(OUT, exist_ok=True); total = 0
    for i, (t, c) in enumerate(todo, 1):
        raw = wm.get(hp.BASE + width_path(man[t][0], 500), raw=True) or wm.get(hp.BASE + hp.thumb_path(man[t][0]), raw=True)
        if not raw: print('no download for', t, flush=True); continue
        try:
            im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((SIZE, SIZE))
            buf = io.BytesIO(); im.save(buf, 'WEBP', quality=QUALITY, method=6)
        except Exception: print('bad image for', t, flush=True); continue
        open(os.path.join(OUT, hosted[t]), 'wb').write(buf.getvalue()); large[t] = hosted[t]; total += len(buf.getvalue())
        print('%3d %-40s %2d places %3dx%-3d %5.1f KB' % (i, t[:40], c, im.size[0], im.size[1], len(buf.getvalue()) / 1024), flush=True)
        if i % 10 == 0: json.dump(large, open(LARGE, 'w'), indent=0, sort_keys=True)
    json.dump(large, open(LARGE, 'w'), indent=0, sort_keys=True)
    print('large copies:', len(large), '; this run', round(total / 1024), 'KB', flush=True)
if __name__ == '__main__': main()
