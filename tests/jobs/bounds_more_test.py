#!/usr/bin/env python3
"""#977: jobs/bounds_more.py writes the credit record of every outline it finds and a miss for every park it does not, and does not retry a miss before its delay is over."""
import datetime, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import bounds_more as bm, outline_records as orc, photo_registry as pr

NOW = datetime.datetime(2026, 11, 16, 12, 0, tzinfo=datetime.timezone.utc)
RING = [(0.0, 0.0), (0.0, 0.1), (0.1, 0.1), (0.1, 0.0), (0.0, 0.0)]


def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f: json.dump(obj, f)


class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(); self.calls = []
        for pid, park in (('wd', True), ('os', True), ('no', True), ('city', False)):
            put(self.root, 'data/places/%s.json' % pid, {'id': pid, 'name': pid.upper() + ' National Park', 'lat': 0.05, 'lon': 0.05, 'park': park})
        self._w, self._c, self._o = bm.wikidata, bm.from_commons, bm.from_osm
        bm.wikidata = lambda e: ('Q1', 'File.map') if e['id'] == 'wd' else (None, None)
        bm.from_commons = lambda f: [RING]
        bm.from_osm = lambda e, qid: ([RING], 'https://nominatim.openstreetmap.org/ui/details.html?osmtype=R&osmid=9') if e['id'] == 'os' else (None, None)
        bm.time.sleep = lambda s: None

    def tearDown(self): bm.wikidata, bm.from_commons, bm.from_osm = self._w, self._c, self._o

    def test_found_outlines_get_a_record_and_the_rest_a_miss(self):
        got, missing = bm.run(root=self.root, now=NOW)
        self.assertEqual(got, 2); self.assertEqual([e['id'] for e in missing], ['no'])
        r = orc.OutlineRecords(self.root)
        self.assertEqual({k: v['source'] for k, v in r.recs.items()}, {'wd': 'wikidata', 'os': 'osm'})
        self.assertEqual(r.recs['wd']['page'], 'https://www.wikidata.org/wiki/Q1'); self.assertIn('osmtype=R', r.recs['os']['page'])
        self.assertEqual(r.miss_['no']['status'], 'none'); self.assertEqual(r.miss_['no']['attempts'], 1)
        self.assertEqual(r.check(), []); self.assertNotIn('city', r.miss_)   # not a park: not looked for

    def test_a_miss_is_not_retried_before_its_delay_and_is_afterwards(self):
        bm.run(root=self.root, now=NOW)
        asked = []; bm.wikidata = lambda e: (asked.append(e['id']), (None, None))[1]
        bm.run(root=self.root, now=NOW + datetime.timedelta(minutes=30)); self.assertEqual(asked, [])
        bm.run(root=self.root, now=NOW + datetime.timedelta(days=8)); self.assertEqual(asked, ['no'])
        self.assertEqual(orc.OutlineRecords(self.root).miss_['no']['attempts'], 2)

    def test_a_found_outline_leaves_the_missing_list(self):
        bm.run(root=self.root, now=NOW); bm.from_osm = lambda e, qid: ([RING], None)
        bm.run(root=self.root, now=NOW + datetime.timedelta(days=8))
        r = orc.OutlineRecords(self.root); self.assertIn('no', r.recs); self.assertNotIn('no', r.miss_); self.assertEqual(r.check(), [])

    def test_a_file_from_the_pad_us_step_gets_its_record(self):
        put(self.root, 'data/outlines/wd.json', {'n': 'x', 'r': [[0, 0, 0, 1, 1, 1, 0, 0]]})   # no `s`: PAD-US
        bm.run(root=self.root, now=NOW); self.assertEqual(orc.OutlineRecords(self.root).recs['wd']['source'], 'padus')


if __name__ == '__main__': unittest.main()
