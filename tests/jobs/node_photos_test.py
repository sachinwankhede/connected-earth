#!/usr/bin/env python3
"""#976: the writer for the pictures of non-species nodes (lib/node_photos.py)."""
import os, sys, tempfile, unittest, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
import node_photos as np

NOW = datetime.datetime(2026, 11, 16, 12, 0, tzinfo=datetime.timezone.utc)
ROW = {'a': 'Jane Doe', 'l': 'CC BY-SA 4.0', 'lu': 'https://creativecommons.org/licenses/by-sa/4.0/', 'p': 'https://commons.wikimedia.org/wiki/File:Sunbeam.jpg', 'page': 'Sunbeam', 'wiki': 'Sunbeam'}


class NodeIdTests(unittest.TestCase):
    def test_the_id_is_the_slug_of_the_concept_title(self):
        self.assertEqual(np.node_id('Sunbeam'), 'sunbeam')
        self.assertEqual(np.node_id('North American Monsoon'), np.node_id('North American monsoon'))
        self.assertEqual(np.node_id(' Soil  (science) '), 'soil-science')


class WriterTests(unittest.TestCase):
    def setUp(self): self.root = tempfile.mkdtemp()

    def test_a_stored_picture_has_its_file_row_and_dates_and_no_expiry(self):
        w = np.NodePhotos(self.root); w.put('sunbeam', ROW, b'webp-1', NOW); w.commit()
        r = np.NodePhotos(self.root); e = r.pics['sunbeam']
        self.assertTrue(os.path.exists(os.path.join(self.root, 'photos', 'nodes', e['f'])))
        self.assertEqual((e['built'], e['checkedAt']), (NOW.isoformat(), NOW.isoformat())); self.assertNotIn('expires', e)
        self.assertEqual(r.check(), [])

    def test_a_new_picture_replaces_the_old_file_and_keeps_the_built_date(self):
        w = np.NodePhotos(self.root); w.put('rain', ROW, b'a', NOW); w.commit()
        later = NOW + datetime.timedelta(days=30); w = np.NodePhotos(self.root); w.put('rain', dict(w.pics['rain']), b'b', later); w.commit()
        r = np.NodePhotos(self.root); self.assertEqual(len(os.listdir(os.path.join(self.root, 'photos', 'nodes'))), 1)
        self.assertEqual((r.pics['rain']['built'], r.pics['rain']['checkedAt']), (NOW.isoformat(), later.isoformat())); self.assertEqual(r.check(), [])

    def test_a_file_two_concepts_share_stays_until_both_drop_it(self):
        w = np.NodePhotos(self.root); w.put('rain', ROW, b'same', NOW); w.put('precipitation', ROW, b'same', NOW); w.commit()
        w = np.NodePhotos(self.root); w.remove('rain', 'no_image'); w.commit()
        self.assertEqual(len(os.listdir(os.path.join(self.root, 'photos', 'nodes'))), 1, 'the other concept still shows it')

    def test_a_concept_with_a_picture_cannot_be_missing_and_a_bad_id_is_refused(self):
        w = np.NodePhotos(self.root); w.put('soil', ROW, b'x', NOW)
        with self.assertRaises(ValueError): w.miss('soil', 'no_image')
        with self.assertRaises(ValueError): w.put('Desert soil', ROW, b'y', NOW)
        with self.assertRaises(ValueError): w.put('fire', dict(ROW, l='CC BY 4.0', a='Unknown'), b'z', NOW)

    def test_check_finds_a_missing_file_an_unlisted_file_and_repair_fixes_both(self):
        w = np.NodePhotos(self.root); w.put('snow', ROW, b'q', NOW); w.commit()
        os.remove(os.path.join(self.root, 'photos', 'nodes', w.pics['snow']['f']))
        with open(os.path.join(self.root, 'photos', 'nodes', 'stray.webp'), 'wb') as f: f.write(b'1')
        r = np.NodePhotos(self.root); self.assertEqual(len(r.check()), 2)
        r.repair(); self.assertEqual(np.NodePhotos(self.root).check(), [])


if __name__ == '__main__': unittest.main()
