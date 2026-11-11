#!/usr/bin/env python3
"""#406 step 4: every kind of data file the build ships is read by the app, or is on a short list of files known to be unread (with the item that will read them).
A new shipped file nobody reads is a cost with no use; this fails until it is read or listed here on purpose."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

# the app is src/app.html plus the pieces it includes, joined the way the build does
SRC = os.path.join(ROOT, 'src')
app = open(os.path.join(SRC, 'app.html')).read()
app = re.sub(r'^__INCLUDE:([\w./-]+)__\n', lambda m: open(os.path.join(SRC, m.group(1))).read(), app, flags=re.M)

# files of api/places/<main|pilot>/ that the app reads: it asks for them by name
READ = ['index-world', 'cards-world', 'index-local', 'cards-local', 'counts.json']
# shipped on purpose, not read yet: the per-region cut of the local places is the next step of #313 (the app still loads all local places in one go), the positions files
# are what a later map draw would read. Remove a name from here when the app reads it; a name that is read must not stay here.
KNOWN_UNREAD = ['positions.json', 'positions-local.json']
REGION_FILE = re.compile(r'^(index|cards)-(?!world\.json$|local\.json$)[a-z0-9-]+\.json$')

links, ecos = B.load_places(False)
errs = B.check(ecos, links, B.app_source(), json.load(open(os.path.join(ROOT, 'data', 'geo', 'geo.json'))))
assert not errs, errs[:3]
files = B.split_regions(B.split(ecos, links)[0])

unread = []
for f in sorted(files):
    if REGION_FILE.match(f) or f in KNOWN_UNREAD: continue   # per-region files are one family: see KNOWN_UNREAD note above
    name = f if f == 'counts.json' else f[:-len('.json')]
    assert name in READ, f + ' is shipped but not on the list of files the app reads (add it to READ with its reader, or to KNOWN_UNREAD with the item)'
    if name in ('counts.json',): needle = 'counts.json'
    else: needle = '"' + name + '"'
    assert needle in app, f + ' is on the READ list but the app does not ask for it'
for f in KNOWN_UNREAD:
    assert f in files, f + ' is in KNOWN_UNREAD but the build no longer ships it: remove it from the list'
    assert f not in app, f + ' is read by the app now: remove it from KNOWN_UNREAD'
assert any(REGION_FILE.match(f) for f in files), 'per-region files are shipped (the check above skips them as one family)'
for r in [f for f in files if REGION_FILE.match(f)][:5]:
    assert ('"' + r[:-5] + '"') not in app, r + ' is read by the app now: take the region files off the unread family'

# the other api folders: each one is read through a named call in Data (src/app/data.js), so its path must be in the app
for d in ['api/species/', 'api/species-pictures.json', 'api/species-places', 'api/species-tab', 'api/ties', 'api/search', 'api/journeys']:
    assert d in app or d.replace('api/', '') in app, d + ' is shipped but the app does not read it'
print('shipped files read ok: %d places files, %d known unread' % (len(files), len(KNOWN_UNREAD)))
