#!/usr/bin/env python3
"""#977: the credit records of park outlines (lib/outline_records.py)."""
import json, os, sys, tempfile, unittest, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
import outline_records as orc

NOW = datetime.datetime(2026, 11, 16, 12, 0, tzinfo=datetime.timezone.utc)


def outline(root, pid, **extra):
    os.makedirs(os.path.join(root, 'data', 'outlines'), exist_ok=True)
    with open(os.path.join(root, 'data', 'outlines', pid + '.json'), 'w') as f: json.dump(dict({'n': pid, 'r': [[0, 0, 1, 1]]}, **extra), f)


class RecordTests(unittest.TestCase):
    def setUp(self): self.root = tempfile.mkdtemp()

    def test_a_record_has_the_shared_shape_and_no_author_or_expiry(self):
        outline(self.root, 'akchilkat'); w = orc.OutlineRecords(self.root); w.record('akchilkat', 'padus', now=NOW); w.commit()
        e = orc.OutlineRecords(self.root).recs['akchilkat']
        self.assertEqual(set(e), {'source', 'licence', 'licence link', 'built', 'checkedAt'})
        self.assertEqual((e['built'], e['checkedAt']), (NOW.isoformat(), NOW.isoformat())); self.assertEqual(orc.OutlineRecords(self.root).check(), [])

    def test_replacing_a_record_keeps_built_and_moves_checkedAt(self):
        outline(self.root, 'a1', s='osm'); w = orc.OutlineRecords(self.root); w.record('a1', 'osm', page='https://www.openstreetmap.org/relation/1', now=NOW); w.commit()
        later = NOW + datetime.timedelta(days=30); w = orc.OutlineRecords(self.root); w.record('a1', 'osm', now=later); e = w.recs['a1']
        self.assertEqual((e['built'], e['checkedAt']), (NOW.isoformat(), later.isoformat()))

    def test_drop_removes_file_and_record_and_lists_the_place_as_missing(self):   # #1004
        outline(self.root, 'bad1'); w = orc.OutlineRecords(self.root); w.record('bad1', 'padus', now=NOW); w.commit()
        w = orc.OutlineRecords(self.root); w.drop('bad1', now=NOW); w.commit()
        r = orc.OutlineRecords(self.root); self.assertFalse(r.has('bad1')); self.assertTrue(r.is_missing('bad1')); self.assertFalse(os.path.exists(os.path.join(self.root, 'data', 'outlines', 'bad1.json'))); self.assertEqual(r.check(), [])

    def test_source_of_a_file_is_its_s_or_padus(self):
        self.assertEqual(orc.source_of({'n': 'x'}), 'padus'); self.assertEqual(orc.source_of({'s': 'wikidata'}), 'wikidata')

    def test_unknown_source_and_bad_id_are_refused(self):
        w = orc.OutlineRecords(self.root)
        with self.assertRaises(ValueError): w.record('a1', 'bing')
        with self.assertRaises(ValueError): w.record('Not An Id', 'osm')

    def test_a_place_with_a_record_cannot_be_missing_and_recording_clears_missing(self):
        w = orc.OutlineRecords(self.root); w.miss('p1', 'notyet'); self.assertTrue(w.is_missing('p1'))
        w.record('p1', 'padus', now=NOW); self.assertFalse(w.is_missing('p1'))
        with self.assertRaises(ValueError): w.miss('p1', 'notyet')

    def test_check_finds_each_kind_of_disagreement(self):
        outline(self.root, 'nofile_rec_missing'); outline(self.root, 'wrongsrc', s='osm'); outline(self.root, 'badlic')
        w = orc.OutlineRecords(self.root); w.record('ghost', 'padus', now=NOW); w.record('wrongsrc', 'padus', now=NOW); w.record('badlic', 'padus', now=NOW)
        w.recs['badlic']['licence'] = 'CC BY'; w.commit()
        errs = '\n'.join(orc.OutlineRecords(self.root).check())
        self.assertIn('ghost: has an outline record but', errs); self.assertIn('wrongsrc: record says padus but the file says osm', errs)
        self.assertIn('badlic: licence is not the one', errs); self.assertIn('nofile_rec_missing.json has no record', errs)

    def test_nothing_is_checked_before_the_record_file_exists(self):
        outline(self.root, 'a1'); self.assertEqual(orc.OutlineRecords(self.root).check(), [])


if __name__ == '__main__': unittest.main()
