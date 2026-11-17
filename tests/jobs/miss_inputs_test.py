#!/usr/bin/env python3
"""#887 step 5: a miss records what it was tried with (point, name, title) and stops holding when the place changes."""
import datetime, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import photo_registry as pr, contracts, outline_records as orc

NOW = datetime.datetime(2026, 11, 17, tzinfo=datetime.timezone.utc)
P = {'id': 'a', 'name': 'Honey Creek State Park', 'lat': 40.8312345, 'lon': -92.9, 'imgwiki': 'Honey Creek State Park'}

class T(unittest.TestCase):
    def test_inputs_from_a_place_or_a_unit(self):
        self.assertEqual(pr.place_inputs(P), {'lat': 40.8312, 'lon': -92.9, 'name': 'Honey Creek State Park', 'title': 'Honey Creek State Park'})
        self.assertEqual(pr.place_inputs({'name': 'N', 'title': 'T', 'lat': 1, 'lon': 2})['title'], 'T')

    def test_same_inputs(self):
        a = pr.place_inputs(P)
        self.assertTrue(pr.same_inputs(a, dict(a, lat=a['lat'] + 0.001)))   # about 110 m
        self.assertFalse(pr.same_inputs(a, dict(a, lat=a['lat'] + 0.5)))   # about 55 km
        self.assertFalse(pr.same_inputs(a, dict(a, name='Another')))
        self.assertFalse(pr.same_inputs(a, dict(a, title='Another')))
        self.assertFalse(pr.same_inputs(None, a)); self.assertFalse(pr.same_inputs(a, None))
        self.assertEqual(contracts.INPUT_MOVE_KM, 1.0)

    def test_cache_active_reads_the_inputs_only_when_given_them(self):
        a = pr.place_inputs(P); e = pr.negative_entry('nophoto', 1, NOW, inputs=a); legacy = pr.negative_entry('nophoto', 1, NOW)
        self.assertNotIn('inputs', legacy); self.assertEqual(e['inputs'], a)
        later = NOW + datetime.timedelta(days=1)
        self.assertTrue(pr.cache_active(e, later) and pr.cache_active(legacy, later))   # callers that do not pass inputs: unchanged
        self.assertTrue(pr.cache_active(e, later, inputs=a))
        self.assertFalse(pr.cache_active(legacy, later, inputs=a))   # recorded before inputs were kept: tried once more
        self.assertFalse(pr.cache_active(e, later, inputs=dict(a, lat=a['lat'] + 0.5)))   # the place moved
        self.assertFalse(pr.cache_active(e, NOW + datetime.timedelta(days=400), inputs=a))   # the expiry still applies

    def test_an_outline_miss_keeps_its_inputs(self):
        r = tempfile.mkdtemp(); rec = orc.OutlineRecords(r); rec.miss('a', 'none', now=NOW, inputs=pr.place_inputs(P)); rec.commit()
        self.assertEqual(orc.OutlineRecords(r).miss_['a']['inputs']['name'], 'Honey Creek State Park')
        rec.miss('b', 'none', now=NOW); self.assertNotIn('inputs', rec.miss_['b'])

if __name__ == '__main__': unittest.main()
