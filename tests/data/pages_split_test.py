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
    assert all(f.startswith(('api/species/', 'photos/species-md/', 'photos/species-lg/')) for f in species)
    assert not any(f.startswith(('api/species/', 'photos/species-md/', 'photos/species-lg/')) for f in app)
    assert len(app) < 20000 and len(species) + 1 < 20000, (len(app), len(species))
    assert os.path.exists(os.path.join(ROOT, 'dist', 'pages-species', '_headers'))
    subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'pages_payload.py')], check=True, capture_output=True)   # leave the whole payload in place
else:
    print('payload modes skipped: the build has not run')
print('ok')
