#!/usr/bin/env python3
"""Stage and verify the exact files needed by the GitHub Pages site."""
import json
from pathlib import Path, PurePosixPath
import shutil

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'dist' / 'pages'
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


def copy_file(source, relative, expected):
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    expected.add(target.relative_to(DEST).as_posix())


def place_image_path(filename):
    path = PurePosixPath(filename)
    if path.is_absolute() or '..' in path.parts or '\\' in filename:
        raise SystemExit('unsafe place photo path: ' + filename)
    return path


def main():
    if DEST.exists():
        if DEST.is_dir() and not DEST.is_symlink():
            shutil.rmtree(DEST)
        else:
            DEST.unlink()
    DEST.mkdir(parents=True)
    expected = set()

    for relative in ROOT_FILES:
        copy_file(ROOT / relative, relative, expected)

    for lib in sorted(ROOT.glob('maplibre-gl-*.js')):
        copy_file(lib, lib.name, expected)

    for font in sorted((ROOT / 'fonts').glob('*.woff2')):
        copy_file(font, font.relative_to(ROOT).as_posix(), expected)

    for directory in ('webs', 'data/outlines'):
        source_dir = ROOT / directory
        files = sorted(source_dir.glob('*.json'))
        if not files:
            raise SystemExit('no runtime JSON files found in ' + directory)
        for source in files:
            json.loads(source.read_text())
            copy_file(source, source.relative_to(ROOT).as_posix(), expected)

    for relative in ('photos/species.json', 'photos/species_metadata.json', 'photos/places/places.json'):
        copy_file(ROOT / relative, relative, expected)

    json.loads((DEST / 'photos/species.json').read_text())
    json.loads((DEST / 'photos/species_metadata.json').read_text())
    place_photos = json.loads((ROOT / 'photos/places/places.json').read_text())
    for record in place_photos.values():
        path = place_image_path(record['f'])
        source = ROOT / 'photos/places' / Path(*path.parts)
        if not source.is_file():
            raise SystemExit('missing place photo: ' + record['f'])
        copy_file(source, 'photos/places/' + path.as_posix(), expected)

    manifest = json.loads((DEST / 'manifest.webmanifest').read_text())
    for icon in manifest.get('icons', []):
        if icon['src'] not in expected:
            raise SystemExit('missing manifest icon: ' + icon['src'])

    links = json.loads((ROOT / 'data/links.json').read_text())
    web_ids = set(links['order'])
    web_ids.update(json.loads((ROOT / 'data-auto/order.json').read_text()))
    missing_webs = sorted(web_id for web_id in web_ids if 'webs/' + web_id + '.json' not in expected)
    if missing_webs:
        raise SystemExit('missing generated web JSON: ' + ', '.join(missing_webs[:10]))
    if 'webs/about.json' not in expected:
        raise SystemExit('missing generated species descriptions: webs/about.json')

    runtime_markers = (
        'photos/species.json',
        'photos/species_metadata.json',
        'photos/places/',
        'data/outlines/',
        'webs/',
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
    main()
