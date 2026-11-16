#!/usr/bin/env python3
"""outlinerecords_migrate.py: one-time creation of the credit records of the existing park outlines (#977 step 3; docs/DATA-PLAN.md "Credits"; owner, 16 Nov).

Usage: outlinerecords_migrate.py [dry]
Every data/outlines/<place id>.json gets one row in data/outline_records.json through lib/outline_records.py: the source is the file's own `s` key (`wikidata`, `osm`) or PAD-US when it has none,
the licence is the source's, and the row gets `built` and `checkedAt` (no author, no `expires`). ADDITIVE: no outline file changes. A file whose `s` is a source the writer does not know stops the run.
Refuses when data/outline_records.json already exists. Prints counts per source and checks the round trip (`check()` reports nothing). `dry` writes nothing. Deleted after the migration has run."""
import collections, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outline_records as orc


def plan(root):
    """{place id: source} for every outline file."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, 'data', 'outlines', '*.json'))):
        with open(f) as h: d = json.load(h)
        pid = os.path.basename(f)[:-5]; s = orc.source_of(d)
        if s not in orc.SOURCES: raise SystemExit('%s: unknown outline source %r' % (pid, s))
        out[pid] = s
    return out


def migrate(root, dry=False):
    if os.path.exists(os.path.join(root, *orc.RECORDS)): raise SystemExit('data/outline_records.json already exists: nothing to migrate')
    pl = plan(root); w = orc.OutlineRecords(root)
    for pid, s in pl.items(): w.record(pid, s)
    if not dry: w.commit()
    errs = (orc.OutlineRecords(root).check() if not dry else [])
    if errs: raise SystemExit('round trip failed:\n' + '\n'.join(errs[:20]))
    return pl


if __name__ == '__main__':
    dry = 'dry' in sys.argv[1:]; pl = migrate(ROOT, dry); c = collections.Counter(pl.values())
    print('| Source | Outlines |\n|---|---:|')
    for s in sorted(c): print('| %s | %d |' % (s, c[s]))
    print('\n%d outline records (%s)' % (len(pl), ', '.join('%s %d' % (s, c[s]) for s in sorted(c))))
    print('dry run: nothing written' if dry else 'written: data/outline_records.json')
