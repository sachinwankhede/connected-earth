#!/usr/bin/env python3
"""dropoutlines.py [--dry] id ... (#977): remove the outline of each named place (file and credit record) and put the place on the missing list, so data-outlines looks for a better one
(Wikidata, then OpenStreetMap; PAD-US skips a place on the missing list). For a place whose outline is only one protected unit inside a larger place (owner, 17 Nov: xusia, xusri). No network."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outline_records

def main(ids, root=ROOT, dry=False, now=None):
    rec = outline_records.OutlineRecords(root); done = []
    for pid in ids:
        if not os.path.exists(os.path.join(root, 'data', 'outlines', pid + '.json')): continue
        done.append(pid)
        if not dry: rec.drop(pid, now=now)
    if done and not dry: rec.commit()
    return done

if __name__ == '__main__':
    dry = '--dry' in sys.argv; ids = [a for a in sys.argv[1:] if not a.startswith('--')]
    done = main(ids, dry=dry)
    print('%d outlines %s: %s' % (len(done), 'to drop' if dry else 'dropped', ' '.join(done)))
