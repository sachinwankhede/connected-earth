#!/usr/bin/env python3
"""#1004: jobs/fixoutlinepoints.py moves a point that is a rough sample onto its own outline and drops an outline that is another unit."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import fixoutlinepoints as f, outline_check as oc, outline_records as orc

SQUARE = [10.0, 50.0, 10.2, 50.0, 10.2, 50.2, 10.0, 50.2, 10.0, 50.0]   # a 0.2 degree square

def tree(places):
    root = tempfile.mkdtemp()
    for d in ('places', 'outlines'): os.makedirs(os.path.join(root, 'data', d))
    rec = orc.OutlineRecords(root)
    for pid, (name, lat, lon, oname) in places.items():
        json.dump({'id': pid, 'name': name, 'lat': lat, 'lon': lon}, open(os.path.join(root, 'data', 'places', pid + '.json'), 'w'))
        json.dump({'n': oname, 'r': [SQUARE]}, open(os.path.join(root, 'data', 'outlines', pid + '.json'), 'w')); rec.record(pid, 'padus', inputs={'lat': lat, 'lon': lon, 'name': name})
    rec.commit(); return root

class T(unittest.TestCase):
    def test_kind_and_same_unit(self):
        self.assertEqual([oc.kind(n) for n in ('Routt National Forest', 'Arapaho National Wildlife Refuge', 'Sequoia National Park', 'Loess Hills')], ['forest', 'refuge', 'park', None])
        p = {'name': 'Arapaho National Wildlife Refuge'}
        self.assertFalse(f.same_unit(p, 'Arapaho National Forest')); self.assertTrue(f.same_unit(p, 'Arapaho National Wildlife Refuge'))
        self.assertFalse(f.same_unit(p, 'Arapaho National Wildlife Refuge', km=f.FAR_KM + 1))   # the same name, far away: another place of that name
        self.assertTrue(f.same_unit({'name': 'Loess Hills'}, 'Loess Hills State Forest'))   # no kind on the place: the name decides

    def test_a_point_between_parts_moves_onto_the_outline_and_a_wrong_unit_is_dropped(self):
        root = tree({'rough': ('Rough Park', 50.1, 10.5, 'Rough Park'), 'wrong': ('Wrong Refuge', 50.1, 10.5, 'Wrong National Forest'), 'ok': ('Fine Park', 50.1, 10.1, 'Fine Park')})
        self.assertEqual(sorted(p for _, p in oc.outside(root, 5.0)), ['rough', 'wrong'])
        moved, dropped = f.main(root)
        self.assertEqual([m[0] for m in moved], ['rough']); self.assertEqual([d[0] for d in dropped], ['wrong'])
        self.assertEqual(oc.outside(root, 5.0), [])   # the moved point is inside; the dropped place has no outline left
        e = json.load(open(os.path.join(root, 'data', 'places', 'rough.json'))); self.assertTrue(oc.inside(e['lon'], e['lat'], [SQUARE]))
        r2 = orc.OutlineRecords(root); self.assertEqual(r2.stale(), [])   # the moved place's record now names the new point (step 5b)
        self.assertEqual((r2.recs['rough']['inputs']['lat'], r2.recs['rough']['inputs']['lon']), (round(e['lat'], 4), round(e['lon'], 4)))
        self.assertFalse(os.path.exists(os.path.join(root, 'data', 'outlines', 'wrong.json')))
        rec = orc.OutlineRecords(root); self.assertFalse(rec.has('wrong')); self.assertTrue(rec.is_missing('wrong')); self.assertEqual(rec.check(), [])
        self.assertEqual(f.main(root), ([], []))   # nothing left to do

    def test_dry_changes_nothing(self):
        root = tree({'rough': ('Rough Park', 50.1, 10.5, 'Rough Park')}); before = open(os.path.join(root, 'data', 'places', 'rough.json')).read()
        moved, _ = f.main(root, dry=True); self.assertEqual(len(moved), 1)
        self.assertEqual(open(os.path.join(root, 'data', 'places', 'rough.json')).read(), before)

if __name__ == '__main__': unittest.main()
