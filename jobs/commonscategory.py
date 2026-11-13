#!/usr/bin/env python3
"""commonscategory.py: a picture for places still without one after commonsnearby.py (#675), found through the place's own CATEGORY on Wikimedia Commons.
Usage: commonscategory.py [limit] [--again]
Many small parks have a Commons category (for example "Category:Mill Bluff State Park") whose files carry no coordinates, so the location search never saw them.
For each place title in photos/places/missing.json whose place has no picture file yet:
  1. searches Commons categories for the place name and keeps the first category that is the place itself: its title adds no distinctive word the place name lacks,
     shares at least half of the place's words, names no building, agrees on state / national / county, and has a Park-or-Lake type word when the place name has none (see good_category);
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

KIND = {'state', 'national', 'county', 'city', 'regional', 'provincial'}   # who runs the place: a state park is not a national preserve
# file names that are not a picture of the place: scientific figures, newspaper clippings, portraits
NOTPLACE = __import__('re').compile(r'(?<![a-z])(figure|fig|diagram|chart|poster|newspaper|courier|bulletin|portrait|congressman|senator|surname)s?(?![a-z])', __import__('re').I)

def toks(s):
    """Like n.words but from 3 letters up, so a short extra word such as 'Oak' in 'White Oak Lake' still counts as an extra word."""
    import unicodedata, re
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z]{3,}', s) if w not in n.GENERIC and w not in KIND}

def good_category(cats, name):
    """The first category that is the place itself, else None. After dropping a bracketed note such as "(California)", the category title must
    (1) add no distinctive word the place name lacks ("Baker River, Washington State" is not "Baker Creek State Park"),
    (2) share at least half of the place's distinctive words,
    (3) name no building or business,
    (4) agree on who runs the place (state, national, county ...), and
    (5) when the place name has no word like Park, Lake or Reserve of its own (a bare "Riverside" or "Pickett"), contain one."""
    import re
    want = n.words(name)
    if not want: return None
    kind = {w for w in re.findall(r'[a-z]+', name.lower()) if w in KIND}; has_type = any(w in n.GENERIC and w not in KIND for w in re.findall(r'[a-z]+', name.lower()))
    for cat in cats:
        base = re.sub(r'\s*\([^)]*\)', '', cat); got = n.words(base)
        low = re.findall(r'[a-z]+', base.lower())
        if not got or toks(base) - toks(name) or len(got) * 2 < len(want) or n.BUILDING.search(cat): continue
        if kind and kind != {w for w in low if w in KIND}: continue
        if not has_type and not any(w in n.GENERIC and w not in KIND for w in low): continue
        return cat
    return None

def choose(files, want, info):
    """The first acceptable file, files naming a distinctive word of the place first; None if no file passes."""
    ordered = [f for f in files if want & n.words(f)] + [f for f in files if not want & n.words(f)]
    for fn in ordered:
        if n.BUILDING.search(fn) or NOTPLACE.search(fn): continue
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
        cat = good_category(categories(name), name); files = category_files(cat) if cat else []
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
