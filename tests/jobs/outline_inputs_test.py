#!/usr/bin/env python3
"""#977 step 5b: an outline record stores the place point and name it was built for; a moved or renamed place is stale; jobs/stampoutlines.py gives older records their baseline."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import stampoutlines, outline_records as orc

def tree(with_inputs):
    root = tempfile.mkdtemp()
    for d in ('outlines', 'places'): os.makedirs(os.path.join(root, 'data', d))
    place = {'id': 'a', 'name': 'Alpha Park', 'lat': 40.00001, 'lng': -100.0}
    json.dump(place, open(os.path.join(root, 'data', 'places', 'a.json'), 'w'))
    json.dump({'n': 'Alpha Park', 'r': [[-101, 39, -99, 39, -99, 41, -101, 39]]}, open(os.path.join(root, 'data', 'outlines', 'a.json'), 'w'))
    rec = orc.OutlineRecords(root); rec.record('a', 'padus', inputs=orc.outline_inputs(place) if with_inputs else None); rec.commit(); return root, place

class T(unittest.TestCase):
    def test_a_record_with_inputs_is_whole_and_fresh(self):
        r, _ = tree(True); rec = orc.OutlineRecords(r)
        self.assertEqual(rec.recs['a']['inputs'], {'lat': 40.0, 'lon': -100.0, 'name': 'Alpha Park'}); self.assertEqual(rec.check(), []); self.assertEqual(rec.stale(), [])

    def test_a_record_without_inputs_is_an_error_until_stamped(self):
        r, _ = tree(False); self.assertTrue(any('inputs' in e for e in orc.OutlineRecords(r).check()))
        self.assertEqual(stampoutlines.main(r, dry=True), ['a']); self.assertTrue(any('inputs' in e for e in orc.OutlineRecords(r).check()))
        self.assertEqual(stampoutlines.main(r), ['a']); rec = orc.OutlineRecords(r)
        self.assertEqual(rec.check(), []); self.assertEqual(rec.stale(), []); self.assertEqual(stampoutlines.main(r), [])

    def test_moved_or_renamed_place_is_stale_a_nudge_is_not(self):
        r, p = tree(True); pf = os.path.join(r, 'data', 'places', 'a.json')
        json.dump(dict(p, lat=40.003), open(pf, 'w')); self.assertEqual(orc.OutlineRecords(r).stale(), [])   # 330 m
        json.dump(dict(p, lat=40.5), open(pf, 'w')); self.assertEqual(orc.OutlineRecords(r).stale(), [('a', 'moved')])
        json.dump(dict(p, name='Beta Park'), open(pf, 'w')); self.assertEqual(orc.OutlineRecords(r).stale(), [('a', 'renamed')])

if __name__ == '__main__': unittest.main()
