#!/usr/bin/env python3
"""commonscategory.py: a picture for places still without one after commonsnearby.py (#675), found through the place's own CATEGORY on Wikimedia Commons.
Usage: commonscategory.py [limit] [--again]
Many small parks have a Commons category (for example "Category:Mill Bluff State Park") whose files carry no coordinates, so the location search never saw them.
For each place title in photos/places/missing.json whose place has no picture file yet:
  1. searches Commons categories for the place name and keeps the first category that is the place itself: its title adds no distinctive word the place name lacks,
     shares at least half of the place's words, names no building, agrees on state / national / county, and has a Park-or-Lake type word when the place name has none (see good_category);
     a file whose name names another US state or a country than the place's own region is refused (names_another_place: a Florida park is not the Alabama one);
  2. lists up to 50 files of that category and keeps the first open-licence JPEG (CC0, CC BY, CC BY-SA, public domain: #421) that passes the same checks as commonsplacephotos.pick
     and does not name a building, road, town or sign; files whose name shares a distinctive word with the place come first;
  3. stores it as photos/places/<id>.jpg, adds it to photos/places/places.json (keyed by the place's imgwiki title) and removes the title from missing.json.
Titles with no match stay in missing.json and get today's date in photos/places_category_tried.json (tried again after 90 days). Every match is printed as
'place -> file (category)' so the pull request shows what was matched. Polite pace via wm.py."""
import sys, os, json, datetime, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
import commonsnearby as n
c = n.c; cp = n.cp
OUT = n.OUT; MAN = n.MAN; MISS = n.MISS; DATA = n.DATA; TRIED = 'photos/places_category_tried.json'; RETRY_DAYS = 90
from place_sources import categories, category_files, KIND, NOTPLACE, toks, good_category, US_STATES, OTHER_COUNTRIES, names_another_place, choose   # the rules moved to lib/place_sources.py (#887); imported back so this job and its tests are unchanged

def regions(data_dir):
    """({place id: region text}, {imgwiki title: set of region texts}) from the place files, for the region check and the shared-title check."""
    import glob
    by_id, by_title = {}, {}
    for f in sorted(glob.glob(data_dir + '/*.json')):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); r = e.get('place') or e.get('country') or ''
        by_id[e['id']] = r
        if e.get('imgwiki'): by_title.setdefault(e['imgwiki'], set()).add(r)
    return by_id, by_title

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, tried = load(MAN), load(MISS), load(TRIED); info_by = n.place_info(DATA); region_of, regions_of = regions(DATA)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t in info_by and t not in man and not os.path.exists('%s/%s.jpg' % (OUT, info_by[t][0])) and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'places to try', flush=True); found_n = 0
    for k, t in enumerate(todo, 1):
        pid, name = info_by[t][0], info_by[t][1]; want = n.words(name) | n.words(t)
        import re
        if len(regions_of.get(t, ())) > 1: tried[t] = today.isoformat(); print('  no:', t, '- the same title is used by places in different regions', flush=True); continue
        cat = good_category(categories(name), name, region_of.get(pid, '')); files = category_files(cat) if cat else []
        got = choose(files, want, cp.commons_info(files[:50]), {w for w in re.findall(r'[a-z]+', name.lower()) if w in KIND}, region_of.get(pid, '')) if files else None
        if not got: tried[t] = today.isoformat(); print('  no:', t, '-', ('category ' + cat + ' has no usable file') if cat else 'no matching category', flush=True)
        else:
            b = wm.get(got[4], raw=True)
            if not b: print('  no:', t, '- download failed', flush=True)
            else:
                open('%s/%s.jpg' % (OUT, pid), 'wb').write(b)
                man[t] = c.entry(pid, t, got, datetime.datetime.now(datetime.timezone.utc).isoformat())
                miss.pop(t, None); tried.pop(t, None); found_n += 1
                print('  match: %s -> %s (category %s)' % (t, got[0], cat), flush=True)
        if k % 10 == 0 or k == len(todo):
            for p, d in ((MAN, man), (MISS, miss), (TRIED, tried)): json.dump(d, open(p, 'w'), ensure_ascii=False, indent=0 if p != TRIED else None, sort_keys=(p == TRIED))
            print(k, 'of', len(todo), '| found', found_n, flush=True)
if __name__ == '__main__': main()
