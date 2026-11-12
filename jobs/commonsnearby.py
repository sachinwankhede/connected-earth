#!/usr/bin/env python3
"""commonsnearby.py: a picture for places still without one after commonsplacephotos.py (#675), found by LOCATION on Wikimedia Commons.
Usage: commonsnearby.py [limit] [--again]
For each place title in photos/places/missing.json whose place has no picture file yet:
  1. asks Commons for files geotagged within RADIUS metres of the place's coordinates (up to 30, nearest first);
  2. keeps the nearest file that is an open-licence JPEG (CC0, CC BY, CC BY-SA, public domain: #421), whose name is not a map, logo and so on,
     AND whose file name shares a distinctive word with the place's name (generic words such as Park, State, Lake are ignored), so a
     photo of the next village is not used for the place;
  3. stores it as photos/places/<id>.jpg, adds it to photos/places/places.json (keyed by the place's imgwiki title) and removes the title from missing.json.
Titles with no match stay in missing.json and get today's date in photos/places_nearby_tried.json (tried again after 90 days). Every match is printed as
'place -> file (distance)' so the pull request shows what was matched. Polite pace via wm.py."""
import sys, os, re, json, glob, datetime, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
import commonsplacephotos as c
cp = c.cp
OUT = c.OUT; MAN = c.MAN; MISS = c.MISS; TRIED = 'photos/places_nearby_tried.json'; DATA = c.DATA
RADIUS = 1500; RETRY_DAYS = 90
GENERIC = set('national state park parks lake lakes river rivers mountain mountains mount forest preserve reserve refuge wildlife monument recreation area '
              'historic site seashore lakeshore island islands bay beach beaches creek canyon valley falls trail trails the of and de la los las del'.split())

def words(s):
    """Distinctive lower-case words (4+ letters, ASCII-folded, not generic) of a name or file name."""
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z]{4,}', s) if w not in GENERIC}

def place_info(data_dir):
    """{imgwiki title: (id, name, lat, lon)} of the first place (by id) using each title."""
    out = {}
    for f in sorted(glob.glob(data_dir + '/*.json')):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); t = e.get('imgwiki')
        if t and t not in out and 'lat' in e and 'lon' in e: out[t] = (e['id'], e.get('name', t), e['lat'], e['lon'])
    return out

def nearby(lat, lon):
    """Commons file names (with underscores), nearest first, geotagged within RADIUS metres."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=geosearch&gsnamespace=6&gslimit=30&format=json&gsradius=%d&gscoord=%s%%7C%s'
         % (RADIUS, lat, lon))
    j = wm.get(q) or {}
    return [(g['title'][5:].replace(' ', '_'), g.get('dist', 0)) for g in (j.get('query') or {}).get('geosearch', [])]

def match(name, title, cands, info):
    """(pick tuple, distance) for the nearest candidate that passes the same checks as commonsplacephotos.pick and shares a distinctive word with the place name; else None."""
    want = words(name) | words(title)
    for fn, dist in cands:
        if not (want & words(fn)): continue
        got = c.pick([fn], info)
        if got: return got, dist
    return None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, tried = load(MAN), load(MISS), load(TRIED); info_by = place_info(DATA)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t in info_by and t not in man and not os.path.exists('%s/%s.jpg' % (OUT, info_by[t][0])) and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'places to try', flush=True); found_n = 0
    for k, t in enumerate(todo, 1):
        pid, name, lat, lon = info_by[t]
        cands = nearby(lat, lon); files = [fn for fn, _ in cands if (words(name) | words(t)) & words(fn)]
        inf = cp.commons_info(files[:50]) if files else {}
        m = match(name, t, cands, inf)
        if not m: tried[t] = today.isoformat(); print('  no:', t, '-', len(cands), 'files nearby,', len(files), 'with a matching name word', flush=True)
        else:
            got, dist = m; b = wm.get(got[4], raw=True)
            if not b: print('  no:', t, '- download failed', flush=True)
            else:
                open('%s/%s.jpg' % (OUT, pid), 'wb').write(b)
                man[t] = c.entry(pid, t, got, datetime.datetime.now(datetime.timezone.utc).isoformat())
                miss.pop(t, None); tried.pop(t, None); found_n += 1
                print('  match: %s -> %s (%d m)' % (t, got[0], dist), flush=True)
        if k % 10 == 0 or k == len(todo):
            for p, d in ((MAN, man), (MISS, miss), (TRIED, tried)): json.dump(d, open(p, 'w'), ensure_ascii=False, indent=0 if p != TRIED else None, sort_keys=(p == TRIED))
            print(k, 'of', len(todo), '| found', found_n, flush=True)
if __name__ == '__main__': main()
