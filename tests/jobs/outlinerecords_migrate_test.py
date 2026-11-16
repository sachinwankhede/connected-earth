#!/usr/bin/env python3
"""#977: the one-time migration that records the existing outlines (jobs/outlinerecords_migrate.py)."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outlinerecords_migrate as m
import outline_records as orc


def put(root, pid, **extra):
    os.makedirs(os.path.join(root, 'data', 'outlines'), exist_ok=True)
    with open(os.path.join(root, 'data', 'outlines', pid + '.json'), 'w') as f: json.dump(dict({'n': pid, 'r': [[0, 0, 1, 1]]}, **extra), f)


class MigrateTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(); put(self.root, 'a1'); put(self.root, 'b2', s='osm'); put(self.root, 'c3', s='wikidata')

    def test_each_outline_gets_the_source_its_file_names(self):
        pl = m.migrate(self.root); self.assertEqual(pl, {'a1': 'padus', 'b2': 'osm', 'c3': 'wikidata'})
        r = orc.OutlineRecords(self.root); self.assertEqual({k: v['source'] for k, v in r.recs.items()}, pl); self.assertEqual(r.check(), [])

    def test_a_dry_run_writes_nothing(self):
        m.migrate(self.root, dry=True); self.assertFalse(os.path.exists(os.path.join(self.root, 'data', 'outline_records.json')))

    def test_it_refuses_to_run_twice(self):
        m.migrate(self.root)
        with self.assertRaises(SystemExit): m.migrate(self.root)

    def test_an_unknown_source_stops_the_run(self):
        put(self.root, 'd4', s='bing')
        with self.assertRaises(SystemExit): m.migrate(self.root)


if __name__ == '__main__': unittest.main()
