#!/usr/bin/env python3
"""Which real places and journeys does each fixture-based browser test name that the fixture does not have? (#821)

Static, no browser: a quoted word in a test file that is the id of a real place or journey but is missing from
tests/fixtures/data is a likely fixture gap. A hint, not proof: a word can also be ordinary text. Only file names are listed,
no data is read. Run: python3 tests/fixtures/check_needs.py [test files...]; exit 1 when a gap is found."""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ids = lambda base, sub: {f[:-5] for f in os.listdir(os.path.join(base, 'data', sub)) if f.endswith('.json')} if os.path.isdir(os.path.join(base, 'data', sub)) else set()
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'data')
real = {'place': ids(ROOT, 'places'), 'journey': ids(ROOT, 'journeys')}
have = {'place': ids(FIX, 'places'), 'journey': ids(FIX, 'journeys')}
COMMON = {'test', 'usa', 'more', 'city', 'park', 'water', 'fire', 'ice'}   # ids that are also plain words
files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'tests', 'app', '*.test.mjs')))
bad = 0
for f in files:
    src = open(f, encoding='utf8').read()
    if 'FMAIN' not in src and 'FPILOT' not in src and 'fixture: true' not in src:
        continue   # still on the real build
    words = set(re.findall(r"""['"`#&=/ ,(]([a-z][a-z0-9]{3,})(?=['"`&,) /.])""", src))
    gaps = []
    for kind in ('place', 'journey'):
        for w in sorted(words):
            if w in real[kind] and w not in have[kind] and w not in COMMON and w not in (have['place'] | have['journey']):
                gaps.append(f'{kind} {w}')
    if gaps:
        bad += 1
        print(f'{os.path.relpath(f, ROOT)}: not in the fixture: ' + ', '.join(gaps))
print('no gaps found' if not bad else f'{bad} file(s) name places or journeys the fixture lacks (a hint; check each)')
sys.exit(1 if bad else 0)
