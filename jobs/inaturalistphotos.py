#!/usr/bin/env python3
"""inaturalistphotos.py: a picture for species that Wikipedia, Wikidata, Commons, GBIF and Openverse have none for (#511), from iNaturalist's taxon photos (api.inaturalist.org).
Usage: inaturalistphotos.py [limit] [--again] [--dry]
Owner decision 12 Nov 2026 (#511): iNaturalist is allowed for this one job, CC0, CC BY and CC BY-SA photos only (never NC, ND or all rights reserved).
For each title in photos/species_missing.json that has no manifest entry yet and is not a row marked abiotic:
  1. looks the Latin name up (api.inaturalist.org/v1/taxa?q=) and keeps a taxon only when its scientific name is exactly the title (a species or genus, active);
  2. reads that taxon's photos (api.inaturalist.org/v1/taxa/<id>) and keeps the first whose licence is CC0, CC BY or CC BY-SA, that has a named photographer,
     is not flagged, and is hosted on inaturalist-open-data.s3.amazonaws.com (the bucket that holds only openly licensed photos);
  3. downloads the medium picture from that bucket and shrinks it to 96 px WebP in photos/species/<id>.webp.
A kept picture is written like an Openverse one: ['inaturalist/<photo id>', page] in photos/species.json, hosted, credited (photographer, licence, https://www.inaturalist.org/photos/<id>) and source 'inaturalist';
it leaves species_missing.json. Titles with no usable picture get today's date in photos/species_inaturalist_tried.json and are tried again only after 90 days.
iNaturalist asks for at most about one request a second: wm.get keeps a 2 s gap. Stops at once when three requests in a row fail. --dry prints what would be kept and writes nothing."""
import sys, os, re, json, datetime, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm, gbifphotos as g, openversephotos as o
MAN, MISS, SRC = g.MAN, g.MISS, g.SRC; HOSTED, META, OUT = g.HOSTED, g.META, g.OUT
TRIED = 'photos/species_inaturalist_tried.json'
RETRY_DAYS = 90; TRY_FILES = 3
API = 'https://api.inaturalist.org/v1/taxa'
BUCKET = 'https://inaturalist-open-data.s3.amazonaws.com/photos/'
RANKS = ('species', 'genus')
LICENCES = {'cc0': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'), 'cc-by': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'),
            'cc-by-sa': ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0')}   # iNaturalist shows its CC licences as version 4.0
def match_taxon(results, name):
    """Id of the active taxon whose scientific name is exactly `name` (any case) and whose rank is a species or genus, else None."""
    for r in results or []:
        if (r.get('name') or '').strip().lower() == name.strip().lower() and r.get('rank') in RANKS and r.get('is_active', True) and isinstance(r.get('id'), int): return r['id']
    return None
def candidates(taxon, limit=TRY_FILES):
    """[(photo id, medium picture link, photographer, short licence, licence link)] in iNaturalist's order, only what may be used."""
    out = []
    for tp in (taxon or {}).get('taxon_photos') or []:
        p = tp.get('photo') or {}; lic = LICENCES.get((p.get('license_code') or '').lower().strip()); pid = p.get('id')
        au = ' '.join(str(p.get('attribution_name') or '').split()); url = p.get('medium_url') or ''
        if not lic or not isinstance(pid, int) or p.get('flags') or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        if url != '%s%d/medium.jpg' % (BUCKET, pid): continue   # only the bucket of openly licensed photos, only the picture of this id
        out.append((pid, url, au, lic[0], lic[1]))
        if len(out) >= limit: break
    return out
def credit(pid, au, lic, lu):
    """The credit entry for species_metadata.json. 's' is the source name the app shows on the credit line (else it says Wikimedia Commons): the data says it, the build only passes it on."""
    return {'a': au, 'l': lic, 'lu': lu, 'p': 'https://www.inaturalist.org/photos/%d' % pid, 's': 'iNaturalist'}
def lookup(name):
    tid = match_taxon((wm.get(API + '?' + urllib.parse.urlencode({'q': name, 'per_page': 10})) or {}).get('results'), name)
    if tid is None: return None
    return ((wm.get('%s/%d' % (API, tid)) or {}).get('results') or [None])[0]
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv; dry = '--dry' in sys.argv
    limit = int(args[0]) if args else 0
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    man, miss, src, tried, hosted, meta = load(MAN), load(MISS), load(SRC), load(TRIED), load(HOSTED), load(META)
    today = datetime.date.today(); cut = (today - datetime.timedelta(days=RETRY_DAYS)).isoformat()
    skip = o.non_organisms()
    todo = sorted(t for t in miss if t not in man and t.replace('_', ' ') not in skip and (again or tried.get(t, '') <= cut))
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True); os.makedirs(OUT, exist_ok=True); found = 0; fails = 0
    def save():
        if dry: return
        for p, d in ((MAN, man), (MISS, miss), (SRC, src), (TRIED, tried), (HOSTED, hosted), (META, meta)):
            json.dump(d, open(p, 'w'), ensure_ascii=False, **({'indent': 0} if p in (HOSTED, META) else {'separators': (',', ':')}), sort_keys=(p in (SRC, TRIED, HOSTED, META)))
    for i, t in enumerate(todo, 1):
        name = t.replace('_', ' '); why = ''
        try:
            taxon = lookup(name); fails = 0
            cs = candidates(taxon) if taxon else []; why = 'no taxon of that name' if not taxon else '%d usable photos' % len(cs)
            for pid, url, au, lic, lu in cs:
                webp = g.fetch_small(url)
                if not webp: why += '; %d too small or not an image' % pid; continue
                print('  yes:', t, '|', lic, '|', au, '| https://www.inaturalist.org/photos/%d' % pid, flush=True)
                if dry: found += 1; why = ''; break
                f = g.fid(t) + '.webp'; open(os.path.join(OUT, f), 'wb').write(webp)
                man[t] = ['inaturalist/%d' % pid, urllib.parse.quote(t.replace(' ', '_'))]; hosted[t] = f; src[t] = 'inaturalist'
                meta[t] = credit(pid, au, lic, lu)
                miss.pop(t, None); tried.pop(t, None); found += 1; why = ''; break
        except RuntimeError as e:
            fails += 1; print('  retry later:', t, '- request failed:', e, flush=True)
            if fails >= 3: print('STOP: three requests in a row failed (throttled or blocked); nothing more is tried. Ask the owner.', flush=True); save(); sys.exit(2)
            continue   # a failed request is not a "no picture": it is not remembered
        if t not in man: tried[t] = today.isoformat(); print('  no:', t, '-', why, flush=True)
        if i % 10 == 0 or i == len(todo): save(); print(i, 'of', len(todo), '| found', found, flush=True)
if __name__ == '__main__': main()
