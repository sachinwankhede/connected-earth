#!/usr/bin/env python3
"""commonscategory.py: a picture for places still without one after commonsnearby.py (#675), found through the place's own CATEGORY on Wikimedia Commons.
Usage: commonscategory.py [limit] [--again]
Many small parks have a Commons category (for example "Category:Mill Bluff State Park") whose files carry no coordinates, so the location search never saw them.
For each place title in photos/places/missing.json whose place has no picture file yet:
  1. searches Commons categories for the place name and keeps the first category whose title shares at least half of the place name's distinctive words
     (generic words such as Park, State, Lake are ignored) and does not name a building or business;
  2. lists up to 50 files of that category and keeps the first open-licence JPEG (CC0, CC BY, CC BY-SA, public domain: #421) that passes the same checks as commonsplacephotos.pick
     and does not name a building, road, town or sign; files whose name shares a distinctive word with the place come first;
  3. stores it as photos/places/<id>.jpg, adds it to photos/places/places.json (keyed by the place's imgwiki title) and removes the title from missing.json.
Titles with no match stay in missing.json and get today's date in photos/places_category_tried.json (tried again after 90 days). Every match is printed as
'place -> file (category)' so the pull request shows what was matched. Polite pace via wm.py."""
import sys, os, json, datetime, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import wm
import commonsnearby as n
c = n.c; cp = n.cp
OUT = n.OUT; MAN = n.MAN; MISS = n.MISS; DATA = n.DATA; TRIED = 'photos/places_category_tried.json'; RETRY_DAYS = 90

def categories(name):
    """Commons category titles (without the 'Category:' prefix), best search hit first."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=14&srlimit=5&format=json&srsearch=%s' % urllib.parse.quote(name))
    j = wm.get(q) or {}
    return [h['title'][9:] for h in (j.get('query') or {}).get('search', []) if h.get('title', '').startswith('Category:')]

def category_files(cat):
    """File names (with underscores) in a category, up to 50."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtype=file&cmlimit=50&format=json&cmtitle=%s' % urllib.parse.quote('Category:' + cat))
    j = wm.get(q) or {}
    return [m['title'][5:].replace(' ', '_') for m in (j.get('query') or {}).get('categorymembers', [])]

def good_category(cats, want):
    """The first category title sharing at least half of the place's distinctive words and naming no building or business, else None."""
    need = (len(want) + 1) // 2
    for cat in cats:
        if want and len(want & n.words(cat)) >= need and not n.BUILDING.search(cat): return cat
    return None

def choose(files, want, info):
    """The first acceptable file, files naming a distinctive word of the place first; None if no file passes."""
    ordered = [f for f in files if want & n.words(f)] + [f for f in files if not want & n.words(f)]
    for fn in ordered:
        if n.BUILDING.search(fn): continue
        got = c.pick([fn], info)
        if got: return got
    return None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, tried = load(MAN), load(MISS), load(TRIED); info_by = n.place_info(DATA)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    todo = sorted(t for t in miss if t in info_by and t not in man and not os.path.exists('%s/%s.jpg' % (OUT, info_by[t][0])) and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'places to try', flush=True); found_n = 0
    for k, t in enumerate(todo, 1):
        pid, name = info_by[t][0], info_by[t][1]; want = n.words(name) | n.words(t)
        cat = good_category(categories(name), want); files = category_files(cat) if cat else []
        got = choose(files, want, cp.commons_info(files[:50])) if files else None
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
