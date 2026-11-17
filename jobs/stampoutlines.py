#!/usr/bin/env python3
"""stampoutlines.py [--dry]: one-off (#977, step 5b). Give each outline record that has no `inputs` the place point and name the outline stands for today.
These outlines were accepted against the place's current point (lib/outline_check.py fails a point more than 5 km outside), so today's point is the honest baseline; from here a moved or renamed place shows as stale.
Nothing else on the record changes (built, checkedAt stay). New outlines get their inputs from the job that writes them."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outline_records as orc


def main(root=ROOT, dry=False):
    rec = orc.OutlineRecords(root); done = []
    for pid, e in sorted(rec.recs.items()):
        if isinstance(e.get('inputs'), dict): continue
        pf = os.path.join(root, 'data', 'places', pid + '.json')
        if not os.path.exists(pf): continue
        e['inputs'] = orc.outline_inputs(json.load(open(pf))); done.append(pid)
    if done and not dry: rec.commit()
    return done


if __name__ == '__main__':
    d = main(dry='--dry' in sys.argv); print('%d record(s) stamped%s' % (len(d), ' (dry run)' if '--dry' in sys.argv else ''))
