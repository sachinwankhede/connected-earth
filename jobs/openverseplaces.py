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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
import openversephotos as o
import commonsplacephotos as cp
OUT = 'photos/places'; MAN = OUT + '/places.json'; MISS = OUT + '/missing.json'; TRIED = 'photos/places_openverse_tried.json'; DATA = 'data/places'
RETRY_DAYS = 90
from place_sources import TRY_FILES, MIN_SIDE, WIDTH, MAX_BYTES, names_place, reject_reasons, to_jpeg   # the rules moved to lib/place_sources.py (#887); imported back so this job and its tests are unchanged
from place_sources import state_of_place as where_of, openverse_candidates as candidates, openverse_search as search, openverse_entry as entry

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
