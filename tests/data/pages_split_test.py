#!/usr/bin/env python3
"""Item #692: the species files can be published apart from the app (Cloudflare Pages holds at most 20,000 files per project).
Checks: the default build text is unchanged without SPECIES_BASE, the address is filled in with it, a bad address is refused, and the three payload modes
split the same files without overlap and each stays under the limit."""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

os.environ.pop('SPECIES_BASE', None)
src = 'json(__SPECIES_ROOT__ + "api/species/" + id) setSpeciesBase(__SPECIES_PHOTOS__ + "photos/species-md/")'
out = B.species_address(src)
assert out.startswith('json(root + "api/species/"'), out
assert 'location.pathname' in out and '__SPECIES' not in out, out

os.environ['SPECIES_BASE'] = 'https://connected-earth-species.pages.dev'
assert B.species_base() == 'https://connected-earth-species.pages.dev/'
out = B.species_address(src)
assert out.count('"https://connected-earth-species.pages.dev/"') == 2 and 'location.pathname' not in out, out
for bad in ('http://x.example/', 'javascript:alert(1)', 'https://x.example/"; evil("', 'species.example.com'):
    os.environ['SPECIES_BASE'] = bad
    try:
        B.species_base()
    except SystemExit:
        continue
    raise AssertionError('accepted a bad SPECIES_BASE: ' + bad)
os.environ.pop('SPECIES_BASE', None)

# Every address the app builds on the species host must be one the species payload publishes: with the split deploy the app asks SPECIES_BASE for it, and a path published
# only on the app's own host is a 404 there (the journey covers were, 15 Nov: the pictures never showed on the live site). The journey covers are not species files: the app
# reads them from its own address and they are published with the app, so none of the species addresses may be a journey folder.
import glob, re
import pages_payload as PP
used = set()
for f in glob.glob(os.path.join(ROOT, 'src', 'app', '*.js')) + glob.glob(os.path.join(ROOT, 'src', '*.js')):
    used |= set(re.findall(r'__SPECIES_(?:PHOTOS|ROOT)__ \+ "([^"]+)"', open(f, encoding='utf-8').read()))
assert any(u.startswith('photos/species-md/') for u in used), used   # the scan finds the species pictures
assert not any('journeys' in u for u in used), 'the app reads a journey cover from the species address: journey covers are published with the app'
for u in sorted(used):
    assert PP.is_species_file(u + 'x'), 'the app reads %s from the species address but pages_payload.py publishes it on the app address (add it to SPECIES_PREFIXES)' % u

if os.path.exists(os.path.join(ROOT, 'index.html')) and os.path.isdir(os.path.join(ROOT, 'api', 'places', 'main')):
    def files(mode, folder):
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'pages_payload.py'), '--mode', mode], capture_output=True, text=True)
        assert r.returncode == 0, mode + ' failed: ' + (r.stdout + r.stderr)[-400:]
        base = os.path.join(ROOT, 'dist', folder)
        return {os.path.relpath(os.path.join(d, f), base) for d, _, fs in os.walk(base) for f in fs}
    everything, app, species = files('all', 'pages'), files('app', 'pages'), files('species', 'pages-species')
    species.discard('_headers')
    assert not (app & species), 'a file is in both payloads'
    assert app | species == everything, 'the two payloads do not add up to the whole site'
    assert all(f.startswith(PP.SPECIES_PREFIXES) for f in species)
    assert not any(f.startswith(PP.SPECIES_PREFIXES) for f in app)
    assert not any(f.startswith(('photos/journeys/', 'photos/journeys-lg/')) for f in species), 'journey covers are in the species payload'
    if os.path.exists(os.path.join(ROOT, 'photos', 'journey_pictures.json')):
        assert any(f.startswith('photos/journeys/') for f in app), 'the journey covers are not in the app payload'
    assert len(app) < 20000 and len(species) + 1 < 20000, (len(app), len(species))
    assert os.path.exists(os.path.join(ROOT, 'dist', 'pages-species', '_headers'))
    subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'pages_payload.py')], check=True, capture_output=True)   # leave the whole payload in place
else:
    print('payload modes skipped: the build has not run')
print('ok')
