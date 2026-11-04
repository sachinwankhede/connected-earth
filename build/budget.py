#!/usr/bin/env python3
"""budget.py: fail if the built pages or data grow past agreed sizes (bytes, uncompressed). Raise a limit on purpose, in this file."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITS = {'index.html': 3_600_000, 'pilot/index.html': 4_200_000}
SPECIES_ROWS_TOTAL = 4_000_000   # data/species/rows/: every species row file together (#276; it was one 4 MB file)
TAXONOMY_MAX = 2_000_000   # data/species/taxonomy.json and taxonomy_review.json together (#254; not published, only the deploy and the validator read them)
WEB_MAX = 250_000      # one place's web file
ABOUT_MAX = 1_200_000   # api/species/: all the species description files together (each is fetched alone, when its sheet opens)
ABOUT_ONE_MAX = 4_000   # one species description file
WEBS_TOTAL = 25_000_000       # fetched one at a time, so only the deploy size grows
OUTLINE_MAX = 400_000   # one park's outline file (fetched when the park opens)
OUTLINES_TOTAL = 20_000_000
bad = 0
def size(p): return os.path.getsize(os.path.join(ROOT, p))
for p, lim in LIMITS.items():
    n = size(p); ok = n <= lim; bad += not ok
    print('%-22s %9d / %9d %s' % (p, n, lim, 'ok' if ok else 'OVER'))
rt = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(os.path.join(ROOT, 'data', 'species', 'rows')) for f in fs)
bad += rt > SPECIES_ROWS_TOTAL
print('%-22s %9d / %9d %s' % ('data/species/rows/ total', rt, SPECIES_ROWS_TOTAL, 'ok' if rt <= SPECIES_ROWS_TOTAL else 'OVER'))
tx = sum(size('data/species/' + f) for f in ('taxonomy.json', 'taxonomy_review.json') if os.path.exists(os.path.join(ROOT, 'data', 'species', f)))
bad += tx > TAXONOMY_MAX
print('%-22s %9d / %9d %s' % ('species taxonomy files', tx, TAXONOMY_MAX, 'ok' if tx <= TAXONOMY_MAX else 'OVER'))
ws = [(f, size('api/' + f)) for f in os.listdir(os.path.join(ROOT, 'api')) if os.path.isfile(os.path.join(ROOT, 'api', f))]
tot = sum(n for _, n in ws); big = max(ws, key=lambda x: x[1])
os_ = [(f, size('data/outlines/' + f)) for f in os.listdir(os.path.join(ROOT, 'data', 'outlines'))]
obig = max(os_, key=lambda x: x[1]); otot = sum(n for _, n in os_)
ab = [size('api/species/' + f) for f in os.listdir(os.path.join(ROOT, 'api', 'species'))]
for label, n, lim in (('species descriptions (api/species/, total)', sum(ab), ABOUT_MAX), ('largest species description file', max(ab), ABOUT_ONE_MAX), ('webs total', tot, WEBS_TOTAL), ('largest web ' + big[0], big[1], WEB_MAX), ('outlines total', otot, OUTLINES_TOTAL), ('largest outline ' + obig[0], obig[1], OUTLINE_MAX)):
    ok = n <= lim; bad += not ok
    print('%-22s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
SEARCH_WORDS_MAX = 60_000     # api/search[-pilot]/w-<two letters>.json: one bucket of the word list, fetched when a query starts with those letters (#260)
SEARCH_ROWS_MAX = 60_000      # api/search[-pilot]/rows-<n>.json: result lines of 256 places
SEARCH_TOTAL_MAX = 2_000_000  # one search folder, all files (only the deploy size grows)
for d in ('search', 'search-pilot'):
    fs = [(f, size('api/%s/%s' % (d, f))) for f in os.listdir(os.path.join(ROOT, 'api', d))]
    for label, n, lim in (('api/%s/ total' % d, sum(n for _, n in fs), SEARCH_TOTAL_MAX), ('api/%s/ largest w-*' % d, max(n for f, n in fs if f.startswith('w-')), SEARCH_WORDS_MAX), ('api/%s/ largest rows-*' % d, max(n for f, n in fs if f.startswith('rows-')), SEARCH_ROWS_MAX)):
        ok = n <= lim; bad += not ok
        print('%-30s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
SPECIES_PLACES_ONE_MAX = 40_000       # api/species-places[-pilot]/<two letters>.json: the places of every species with those first letters, fetched when a species is selected (#253)
SPECIES_PLACES_TOTAL_MAX = 1_500_000  # one folder, all files (only the deploy size grows)
for d in ('species-places', 'species-places-pilot'):
    fs = [size('api/%s/%s' % (d, f)) for f in os.listdir(os.path.join(ROOT, 'api', d))]
    for label, n, lim in (('api/%s/ total' % d, sum(fs), SPECIES_PLACES_TOTAL_MAX), ('api/%s/ largest' % d, max(fs), SPECIES_PLACES_ONE_MAX)):
        ok = n <= lim; bad += not ok
        print('%-30s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
TIES_ONE_MAX = 250_000        # api/ties[-pilot]/<region>.json: the ties of every place of a region, fetched on the first tap in that region (the world file is the largest; #252)
TIES_TOTAL_MAX = 1_000_000    # one folder, all files (only the deploy size grows)
for d in ('ties', 'ties-pilot'):
    fs = [size('api/%s/%s' % (d, f)) for f in os.listdir(os.path.join(ROOT, 'api', d))]
    for label, n, lim in (('api/%s/ total' % d, sum(fs), TIES_TOTAL_MAX), ('api/%s/ largest' % d, max(fs), TIES_ONE_MAX)):
        ok = n <= lim; bad += not ok
        print('%-30s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
PLACES_REGION_ONE_MAX = 300_000   # one file in api/places/main|pilot/ (cards-local.json, all local places together, is the largest; item #313)
PLACES_REGION_TOTAL_MAX = 2_000_000   # all files of one folder (only the deploy size grows; a phone fetches a few of them)
for d in ('main', 'pilot'):
    fs = [(f, size('api/places/%s/%s' % (d, f))) for f in os.listdir(os.path.join(ROOT, 'api', 'places', d))]
    for label, n, lim in (('api/places/%s/ total' % d, sum(n for _, n in fs), PLACES_REGION_TOTAL_MAX), ('api/places/%s/ largest file' % d, max(n for _, n in fs), PLACES_REGION_ONE_MAX)):
        ok = n <= lim; bad += not ok
        print('%-30s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
sys.exit(1 if bad else 0)
