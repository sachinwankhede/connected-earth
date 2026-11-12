#!/usr/bin/env python3
"""commonsplacephotos.py: a picture for places Wikipedia gave none (or none usable) for (#675), from Wikidata and Wikimedia Commons.
Usage: commonsplacephotos.py [limit] [--again]
For each place title in photos/places/missing.json (nophoto, notcommons, notphoto, notfree: Wikipedia's own page picture is missing, not on Commons, not a photograph or not free):
  1. follows Wikipedia redirects and asks Wikidata for the item of that page and its image property (P18), 50 titles per request (the same lookups as commonsphotos.py for species);
  2. asks Commons for the file's licence, author and a 330 px thumbnail;
  3. keeps the picture only when the licence is CC0, CC BY, CC BY-SA or public domain (#421) and the file is a JPEG whose name does not say map, logo, diagram and so on.
A kept picture is downloaded to photos/places/<id>.jpg and added to photos/places/places.json in the shape photos.py writes (keyed by the place's own imgwiki title), and the title leaves missing.json.
Titles with no usable picture stay in missing.json and get today's date in photos/places_commons_tried.json, so they are tried again only after 90 days. Resumable; polite pace via wm.py.
The workflow then runs photo_registry.py migrate and validate, as data-photos does."""
import sys, os, json, glob, datetime, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https
import commonsphotos as cp
import photos as pp
OUT = 'photos/places'; MAN = OUT + '/places.json'; MISS = OUT + '/missing.json'; TRIED = 'photos/places_commons_tried.json'; DATA = 'data/places'
RETRY_DAYS = 90
# photos.py's not-a-photo name filter without its bare "arrowhead" (the National Park Service logo, which also says "logo" or is an .svg): a place such as Arrowhead State Park has a real photo with that word in its file name
NOTPHOTO = pp.re.compile(pp.NOTPHOTO.pattern.replace('arrowhead|', '', 1), pp.re.I)

def place_ids(data_dir):
    """{imgwiki title: id of the first place (by id) that uses it}: one picture file per title, as photos.py stores it."""
    out = {}
    for f in sorted(glob.glob(data_dir + '/*.json')):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); t = e.get('imgwiki')
        if t and t not in out: out[t] = e['id']
    return out

def pick(names, info):
    """The first of the (at most two) candidate files that is an open-licence JPEG photo: (file name, licence, author, licence url, thumbnail url) or None."""
    for n in names[:2]:
        lic, author, lu, thumb, mime = info.get(n.replace(' ', '_'), ('', '', '', '', ''))
        if cp.is_photo_type(mime) and cp.open_licence(lic) and thumb and not NOTPHOTO.search(n) and safe_https(thumb.split('?')[0], ALLOWED_IMAGE_HOSTS):
            return n.replace(' ', '_'), lic, author, lu, thumb
    return None

def entry(place_id, page, found, now):
    """The places.json row photos.py writes; migrate adds the measured fields."""
    fn, lic, author, lu, _ = found
    return dict(f=place_id + '.jpg', a=author or 'Unknown author', l=lic or 'See file page', lu=lu,
                p='https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(fn),
                w='https://en.wikipedia.org/wiki/' + urllib.parse.quote(page.replace(' ', '_')), checkedAt=now, fetchedAt=now)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, tried = load(MAN), load(MISS), load(TRIED); ids = place_ids(DATA)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t in ids and t not in man and not os.path.exists('%s/%s.jpg' % (OUT, ids[t])) and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); found_n = 0; why = {}
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; res = cp.resolve(batch); names = cp.wikidata_images(sorted(set(res.values())))
        files = sorted({n.replace(' ', '_') for v in names.values() for n in v[:2]})
        info = cp.commons_info(files) if files else {}
        for t in batch:
            page = res.get(t, t)
            if page not in names: why[t] = 'no Wikidata item for this page (after following redirects)'; tried[t] = today.isoformat(); continue
            got = pick(names[page], info)
            if not got: why[t] = 'no usable picture among %s' % names[page][:2]; tried[t] = today.isoformat(); continue
            b = wm.get(got[4], raw=True)
            if not b: why[t] = 'download failed'; continue   # not marked tried: the next run looks again
            open('%s/%s.jpg' % (OUT, ids[t]), 'wb').write(b)
            man[t] = entry(ids[t], page, got, datetime.datetime.now(datetime.timezone.utc).isoformat())
            miss.pop(t, None); tried.pop(t, None); found_n += 1
        for p, d in ((MAN, man), (MISS, miss), (TRIED, tried)): json.dump(d, open(p, 'w'), ensure_ascii=False, indent=0 if p != TRIED else None, sort_keys=(p == TRIED))
        print(min(i + 50, len(todo)), 'of', len(todo), '| found', found_n, flush=True)
        for t in batch:
            if t not in man: print('  no:', t, '-', why.get(t, '?'), flush=True)
if __name__ == '__main__': main()
