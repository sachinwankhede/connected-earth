#!/usr/bin/env python3
"""Stage and verify the exact files needed by the GitHub Pages site."""
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lib'))
sys.path.insert(0, str(ROOT / 'build'))
import species_pics, journey_pics, node_photos
DEST = ROOT / 'dist' / 'pages'
# The species files (descriptions and the 192 px and 400 px pictures) can be published apart from the app (item #692), because a Cloudflare Pages project holds at most 20,000 files.
# Modes: all (everything in dist/pages, as before; GitHub Pages), app (dist/pages without the species files; the app reads them from SPECIES_BASE), species (only the species files, in dist/pages-species).
MODES = ('all', 'app', 'species')
SPECIES_PREFIXES = ('api/species/', 'photos/species-md/', 'photos/species-lg/')   # journey covers (#934) are not species files: they are published with the app
ROOT_FILES = (
    'index.html',
    'pilot/index.html',
    'sw.js',
    'manifest.webmanifest',
    'apple-touch-icon.png',
    'icon-192.png',
    'icon-512.png',
    'icon-maskable-512.png',
    'robots.txt',
)


MODE = 'all'


def is_species_file(relative):
    return relative.startswith(SPECIES_PREFIXES)


def wanted(relative):
    return MODE == 'all' or (MODE == 'species') == is_species_file(relative)


def copy_file(source, relative, expected):
    if not wanted(relative):
        return
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    expected.add(target.relative_to(DEST).as_posix())


def place_image_path(filename):
    path = PurePosixPath(filename)
    if path.is_absolute() or '..' in path.parts or '\\' in filename:
        raise SystemExit('unsafe place photo path: ' + filename)
    return path


SPECIES_HEADERS = """/*
  Access-Control-Allow-Origin: *
/photos/*
  Cache-Control: public, max-age=31536000, immutable
/api/*
  Cache-Control: public, max-age=3600
"""


def main(mode='all'):
    global MODE, DEST
    if mode not in MODES:
        raise SystemExit('mode must be one of ' + ', '.join(MODES))
    MODE = mode
    if mode == 'species':
        DEST = ROOT / 'dist' / 'pages-species'
    if DEST.exists():
        if DEST.is_dir() and not DEST.is_symlink():
            shutil.rmtree(DEST)
        else:
            DEST.unlink()
    DEST.mkdir(parents=True)
    expected = set()

    for relative in ROOT_FILES:
        copy_file(ROOT / relative, relative, expected)

    copy_file(ROOT / 'geo-states.json', 'geo-states.json', expected)

    if MODE != 'species':   # the data status page and its audit file, made from the data in this checkout (build/status_page.py); not part of the app
        import status_page
        status_page.write(str(DEST))
        expected.update(('status/index.html', 'status/audit.json'))

    for lib in sorted(list(ROOT.glob('maplibre-gl-*.js')) + list(ROOT.glob('d3-*.js')) + list(ROOT.glob('species-tab-*.js')) + list(ROOT.glob('pulse-*.js'))):
        copy_file(lib, lib.name, expected)

    for font in sorted((ROOT / 'fonts').glob('*.woff2')):
        copy_file(font, font.relative_to(ROOT).as_posix(), expected)

    for directory in ('api', 'api/species', 'api/places/main', 'api/places/pilot', 'api/journeys', 'api/search', 'api/search-pilot', 'api/species-places', 'api/species-places-pilot', 'api/species-tab', 'api/species-tab-pilot', 'api/ties', 'api/ties-pilot', 'data/outlines'):
        source_dir = ROOT / directory
        files = sorted(source_dir.glob('*.json'))
        if not files:
            raise SystemExit('no runtime JSON files found in ' + directory)
        for source in files:
            json.loads(source.read_text())
            copy_file(source, source.relative_to(ROOT).as_posix(), expected)

    copy_file(ROOT / 'photos/places/places.json', 'photos/places/places.json', expected)
    # our own copies of the species pictures: the app reads the 192 px (species-md) and 400 px (species-lg) copies. Since #1188 the stored picture is the 192 px file in species-md; an old 96 px file in photos/species/ stays in the repository until the migration (jobs/drop96px.py)
    # (the fallback below, for a picture with no 192 px file) and is not published, which keeps the payload under Cloudflare Pages' 20,000 file limit (#690).
    sp = species_pics.load(str(ROOT)); pics = list(sp['pics'].values()) + list(sp['titles'].values())   # by species id, from either shape; the journeys' pictures are by title (#934)
    hosted_names = {r['f'] for r in pics}
    medium_files = set(sp['medium'].values()) | set(sp['title_medium'].values())   # 192 px tile copies (#669)
    for name in sorted(hosted_names):   # a species without a 192 px copy gets its 96 px file under the same name
        source = ROOT / 'photos/species-md' / name
        if name not in medium_files or not source.is_file():
            source = ROOT / 'photos/species' / name
        copy_file(source, 'photos/species-md/' + name, expected)
    for name in sorted(set(sp['large'].values()) | set(sp['title_large'].values())):   # larger copies (#421)
        source = ROOT / 'photos/species-lg' / name
        if not source.is_file():
            raise SystemExit('larger species picture missing: photos/species-lg/' + name)
        copy_file(source, 'photos/species-lg/' + name, expected)
    jpics = journey_pics.load(str(ROOT))   # the journey covers by journey id (none until photos/journey_pictures.json exists): the cover file (192 px, or 96 px for an old one: same path) and its larger copy
    for row in sorted(jpics['pics'].values(), key=lambda r: r['f']):
        source = ROOT / 'photos/journeys' / row['f']
        if not source.is_file():
            raise SystemExit('journey picture missing: photos/journeys/' + row['f'])
        copy_file(source, 'photos/journeys/' + row['f'], expected)
    for row in sorted(node_photos.NodePhotos(str(ROOT)).pics.values(), key=lambda r: r['f']):   # the pictures of non-species nodes by node id (#976): published with the app, like the journey covers
        source = ROOT / 'photos/nodes' / row['f']
        if not source.is_file():
            raise SystemExit('node picture missing: photos/nodes/' + row['f'])
        copy_file(source, 'photos/nodes/' + row['f'], expected)
    for name in sorted(set(jpics['large'].values())):
        source = ROOT / 'photos/journeys-lg' / name
        if not source.is_file():
            raise SystemExit('larger journey picture missing: photos/journeys-lg/' + name)
        copy_file(source, 'photos/journeys-lg/' + name, expected)
    place_large = json.loads((ROOT / 'photos/places_large.json').read_text()) if (ROOT / 'photos/places_large.json').exists() else {}   # larger copies of the place pictures (#727)
    for name in sorted(set(place_large.values())):
        source = ROOT / 'photos/places-lg' / name
        if not source.is_file():
            raise SystemExit('larger place picture missing: photos/places-lg/' + name)
        copy_file(source, 'photos/places-lg/' + name, expected)
    place_photos = json.loads((ROOT / 'photos/places/places.json').read_text())
    for record in place_photos.values():
        path = place_image_path(record['f'])
        source = ROOT / 'photos/places' / Path(*path.parts)
        if not source.is_file():
            raise SystemExit('missing place photo: ' + record['f'])
        copy_file(source, 'photos/places/' + path.as_posix(), expected)

    if MODE == 'species':   # nothing but the species files, and the header file that lets the app read them from another address
        (DEST / '_headers').write_text(SPECIES_HEADERS)
        expected.add('_headers')
        if not any(name.startswith('api/species/') for name in expected) or not any(name.startswith('photos/species-md/') for name in expected):
            raise SystemExit('the species payload has no descriptions or no pictures')
        actual = {path.relative_to(DEST).as_posix() for path in DEST.rglob('*') if path.is_file()}
        if actual != expected:
            raise SystemExit('staged species payload differs from allowlist; extra=%r missing=%r' % (sorted(actual - expected)[:5], sorted(expected - actual)[:5]))
        print('Species payload verified: %d files, %d bytes' % (len(actual), sum((DEST / path).stat().st_size for path in actual)))
        return
    manifest = json.loads((DEST / 'manifest.webmanifest').read_text())
    for icon in manifest.get('icons', []):
        if icon['src'] not in expected:
            raise SystemExit('missing manifest icon: ' + icon['src'])

    import sys; sys.path.insert(0, str(ROOT / 'build')); import journeydata
    main_ids, pilot_ids = journeydata.order(str(ROOT))
    web_ids = set(main_ids)
    web_ids.update(pilot_ids)
    missing_webs = sorted(web_id for web_id in web_ids if 'api/' + web_id + '.json' not in expected)
    if missing_webs:
        raise SystemExit('missing generated web JSON: ' + ', '.join(missing_webs[:10]))
    for name in ('main/index-world', 'main/cards-world', 'pilot/index-world', 'pilot/cards-world'):   # the app cannot start without its world places files (#313)
        if 'api/places/' + name + '.json' not in expected:
            raise SystemExit('missing places file: api/places/' + name + '.json')
    for name in ('main', 'pilot'):   # the app starts with its journeys file (#377)
        if 'api/journeys/' + name + '.json' not in expected:
            raise SystemExit('missing journeys file: api/journeys/' + name + '.json')
    if MODE == 'all' and not any(name.startswith('api/species/') for name in expected):
        raise SystemExit('missing generated species descriptions: api/species/')

    runtime_markers = (
        'photos/species/',
        'photos/places/',
        'data/outlines/',
        'api/',
        'sw.js',
        'manifest.webmanifest',
    )
    for relative in ('index.html', 'pilot/index.html'):
        html = (DEST / relative).read_text()
        if 'Connected Earth' not in html or 'maplibregl.Map' not in html:
            raise SystemExit('built page is missing app or inline map runtime: ' + relative)
        missing = [marker for marker in runtime_markers if marker not in html]
        if missing:
            raise SystemExit(relative + ' is missing runtime paths: ' + ', '.join(missing))

    actual = {
        path.relative_to(DEST).as_posix()
        for path in DEST.rglob('*')
        if path.is_file()
    }
    if actual != expected:
        extra = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise SystemExit('staged payload differs from allowlist; extra=%r missing=%r' % (extra, missing))

    print('Pages payload verified: %d files, %d bytes' % (
        len(actual), sum((DEST / path).stat().st_size for path in actual)
    ))


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args[args.index('--mode') + 1] if '--mode' in args else 'all')
