#!/usr/bin/env python3
"""One-off for #251 step 2: write country, countries and states of every place file as ids (data/geo/geo.json) and drop `cont` (derived from the country).
Run: python3 build/places_ids.py [--check]   (--check only reports; nothing is written). Safe to run twice."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); import geoids

DUMP = dict(ensure_ascii=False)   # the place files are one line, default separators, no trailing newline

def convert(e):
    if 'country' in e: e['country'] = geoids.country_id(e['country'])
    if 'countries' in e: e['countries'] = [geoids.country_id(c) for c in e['countries']]
    if 'states' in e: e['states'] = [geoids.state_id(s) for s in e['states']]
    e.pop('cont', None)
    return e

def main():
    check = '--check' in sys.argv; changed = bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'places', '*.json'))):
        t = open(f, encoding='utf-8').read(); d = json.loads(t)
        if json.dumps(d, **DUMP) != t: print('format differs, not touched:', f); bad += 1; continue
        n = json.dumps(convert(d), **DUMP)
        if n != t:
            changed += 1
            if not check: open(f, 'w', encoding='utf-8').write(n)
    print('%d files %s, %d left alone' % (changed, 'would change' if check else 'rewritten', bad))

if __name__ == '__main__': main()
