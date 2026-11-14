#!/usr/bin/env python3
"""openverseplaces.py: a picture for US places Wikipedia and Commons gave none for (#768), from Openverse (api.openverse.org).
Usage: openverseplaces.py [limit] [--again] [--dry]
For each place title in photos/places/missing.json that has no manifest entry yet and whose place is "<State>, USA":
  1. searches Openverse images for the place name and the state (category photograph; licences CC0, public domain mark, CC BY, CC BY-SA; iNaturalist excluded);
  2. keeps a result only when its title or tags contain the whole place name AND the state name (a search is not an identity match: a "Trout Pond" in West Virginia is not the one in Maine, #767),
     it has a named creator, the title does not say map, logo, diagram and so on, and it is not a museum or herbarium record;
  3. downloads Openverse's OWN thumbnail (api.openverse.org/v1/images/<id>/thumb/), never the original host, and stores a 330 px wide JPEG as photos/places/<id>.jpg.
A kept picture is added to photos/places/places.json keyed by the place's imgwiki title, credited with its creator, licence and the Openverse page (openverse.org/image/<id>); the workflow then runs
photo_registry.py migrate and validate. Titles with no usable picture get today's date in photos/places_openverse_tried.json and are tried again only after 90 days.
Stops at once when Openverse answers 401 or 403 (a key is needed: ask the owner) or three requests in a row fail. --dry prints what would be kept and writes nothing. Only https links are fetched."""
import sys, os, re, io, json, glob, datetime, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
import openversephotos as o
import commonsplacephotos as cp
OUT = 'photos/places'; MAN = OUT + '/places.json'; MISS = OUT + '/missing.json'; TRIED = 'photos/places_openverse_tried.json'; DATA = 'data/places'
RETRY_DAYS = 90; TRY_FILES = 4; MIN_SIDE = 200; WIDTH = 330; MAX_BYTES = 8_000_000

def where_of(place):
    """The US state name of a place whose `place` field is "<State>, USA", else ''."""
    p = (place or '').strip()
    return p.split(',')[0].strip() if p.endswith(', USA') else ''
def names_place(r, name, state):
    """True when the result's title or tags contain the whole place name and the state name."""
    n, s = o.norm(name), o.norm(state)
    if not n or not s: return False
    blob = [o.norm(r.get('title'))] + [o.norm(t.get('name')) for t in r.get('tags') or []]
    return any(n in b for b in blob) and any(s in b for b in blob)
def candidates(results, name, state):
    """[(id, thumbnail link, creator, short licence, licence link)] in Openverse's order, only what may be used for this place."""
    out = []
    for r in results or []:
        rid = r.get('id') or ''
        if not re.fullmatch(r'[0-9a-f-]{36}', rid) or o.unwanted(r) or cp.NOTPHOTO.search(r.get('title') or '') or not names_place(r, name, state): continue
        lic = o.licence_of(r); au = ' '.join(str(r.get('creator') or '').split())
        if not lic or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        out.append((rid, o.API + rid + '/thumb/', au, lic[0], lic[1]))
    return out
def reject_reasons(results, name, state):
    """{reason: count} for the results candidates() refuses, plus up to 3 example titles that failed only on the place or state words, so a dry run shows why a place found nothing."""
    out = {}; ex = []
    for r in results or []:
        if o.unwanted(r) or cp.NOTPHOTO.search(r.get('title') or ''): k = 'not a photo or unwanted source'
        elif not o.licence_of(r): k = 'licence'
        elif not ' '.join(str(r.get('creator') or '').split()): k = 'no creator'
        elif not names_place(r, name, state):
            k = 'place or state not in title or tags'
            if len(ex) < 3: ex.append(r.get('title') or '')
        else: continue
        out[k] = out.get(k, 0) + 1
    return out, ex
def search(name, state=''):
    """Openverse results for the exact place name. The state is NOT in the query (a phrase plus an extra word returned no result at all for 19 of 20 places in the first dry runs, #768): names_place() checks the state afterwards."""
    q = o.API + '?' + urllib.parse.urlencode({'q': '"%s"' % name, 'license': 'cc0,pdm,by,by-sa', 'category': 'photograph', 'excluded_source': 'inaturalist', 'page_size': 20})
    return (wm.get(q) or {}).get('results') or []
def to_jpeg(raw):
    """A 330 px wide JPEG (bytes), or None when it is too big, not an image, or under 200 px on its short side."""
    from PIL import Image
    if not raw or len(raw) > MAX_BYTES: return None
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
        if min(im.size) < MIN_SIDE: return None
        im = im.convert('RGB')
        if im.size[0] > WIDTH: im = im.resize((WIDTH, max(1, round(im.size[1] * WIDTH / im.size[0]))))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=82); return b.getvalue()
    except Exception: return None
def entry(pid, creator, lic, lu, rid, now):
    page = 'https://openverse.org/image/%s' % rid
    return dict(f=pid + '.jpg', a=creator, l=lic, lu=lu, p=page, w=page, s='Openverse', checkedAt=now, fetchedAt=now)
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv; dry = '--dry' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, tried = load(MAN), load(MISS), load(TRIED)
    ids = cp.place_ids(DATA); info = {}
    for f in glob.glob(DATA + '/*.json'):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); info[e['id']] = e
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t not in man and t in ids and where_of(info[ids[t]].get('place')) and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); found = 0; fails = 0
    def save():
        if dry: return
        json.dump(man, open(MAN, 'w'), ensure_ascii=False, indent=0); json.dump(miss, open(MISS, 'w'), ensure_ascii=False, indent=0)
        json.dump(tried, open(TRIED, 'w'), ensure_ascii=False, indent=0, sort_keys=True)
    for i, t in enumerate(todo, 1):
        before = found; e = info[ids[t]]; name = e.get('short') or e.get('name') or t; state = where_of(e.get('place')); why = ''
        try:
            res = search(name, state); cs = candidates(res, name, state); why = '%d usable photos of %d results' % (len(cs), len(res)); fails = 0
            if not cs and res:
                rr, ex = reject_reasons(res, name, state); why += ' (%s%s)' % (', '.join('%s %d' % (k, n) for k, n in sorted(rr.items())), '; e.g. ' + ' / '.join(ex) if ex else '')
            for rid, url, au, lic, lu in cs[:TRY_FILES]:
                jpg = to_jpeg(wm.get(url, raw=True, tries=2))
                if not jpg: why += '; %s too small or not an image' % rid; continue
                print('  yes:', t, '(%s, %s) |' % (name, state), lic, '|', au, '| https://openverse.org/image/' + rid, flush=True)
                if not dry:
                    os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, ids[t] + '.jpg'), 'wb').write(jpg)
                    man[t] = entry(ids[t], au, lic, lu, rid, datetime.datetime.now(datetime.timezone.utc).isoformat()); miss.pop(t, None); tried.pop(t, None)
                found += 1; why = ''; break
        except RuntimeError as ex:
            fails += 1; print('  retry later:', t, '- request failed:', ex, flush=True)
            if fails >= 3: print('STOP: three requests in a row failed (a key needed, or throttled); nothing more is tried. Ask the owner.', flush=True); save(); sys.exit(2)
            continue
        if found == before: tried[t] = today.isoformat(); print('  no:', t, '-', why, flush=True)
        if i % 10 == 0 or i == len(todo): save(); print(i, 'of', len(todo), '| found', found, flush=True)
if __name__ == '__main__': main()
