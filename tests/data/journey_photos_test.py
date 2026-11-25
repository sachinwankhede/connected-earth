"""lib/journey_photos.py: the one writer for journey covers keeps the file, list row, larger copy and missing record in step (docs/DATA-PLAN.md, "Journey pictures: by journey id")."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import journey_photos as jp

def row(p='https://commons.wikimedia.org/wiki/File:X.jpg'): return {'a': 'Someone', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': p, 'wiki': 'Osprey'}

class WriterTests(unittest.TestCase):
    def setUp(self): self.d = tempfile.mkdtemp(); self.w = jp.JourneyPhotos(self.d)
    def fresh(self): return jp.JourneyPhotos(self.d)
    def read(self, rel):
        with open(os.path.join(self.d, rel), 'rb') as f: return f.read()
    def full(self, jid='osprey'): self.w.put(jid, row(), b'S'); self.w.put_large(jid, b'L'); self.w.commit()

    def test_put_refuses_any_licence_with_no_named_author(self):
        for a in ('', 'Unknown author', 'unknown', 'Anonymous', 'me@example.org'):
            with self.assertRaises(ValueError): self.w.put('osprey', dict(row(), a=a), b'x')
        self.assertFalse(self.w.has('osprey'))
        with self.assertRaises(ValueError): self.w.put('osprey', dict(row(), a='Unknown author', l='CC0'), b'x')   # every licence needs a named author (owner, 25 Nov, #887)
        self.assertFalse(self.w.has('osprey'))
        self.w.put('osprey', dict(row(), a='Jane Roe', l='CC0'), b'x'); self.assertTrue(self.w.has('osprey'))

    def test_author_is_stored_clean(self):
        self.w.put('osprey', dict(row(), a='Jane Roe <jane@example.org>'), b'x'); self.assertEqual(self.w.pics['osprey']['a'], 'Jane Roe')

    def test_put_writes_file_and_row_and_clears_the_miss(self):
        self.w.miss('osprey', 'nophoto', 'commons'); self.w.commit()
        w = self.fresh(); self.assertTrue(w.is_missing('osprey'))
        w.put('osprey', row(), b'WEBP'); w.commit(); w = self.fresh()
        self.assertTrue(w.has('osprey')); self.assertFalse(w.is_missing('osprey')); self.assertNotIn('osprey', w.tried)
        self.assertEqual(w.pics['osprey']['f'], 'osprey.webp'); self.assertEqual(self.read('photos/journeys/osprey.webp'), b'WEBP'); self.assertEqual(w.check(), [])

    def test_two_journeys_with_the_same_title_each_get_their_own_row_and_file(self):
        self.w.put('greenturtleA', row(), b'A'); self.w.put('greenturtleB', row(), b'A'); self.w.commit(); w = self.fresh()
        self.assertEqual(w.check(), []); w.remove('greenturtleA', 'notfree'); w.commit(); w = self.fresh()
        self.assertTrue(w.has('greenturtleB')); self.assertEqual(w.check(), [])

    def test_a_larger_copy_needs_a_stored_picture(self):
        with self.assertRaises(ValueError): self.w.put_large('aa', b'W')
        self.full('aa'); w = self.fresh(); self.assertTrue(w.has_large('aa')); self.assertEqual(w.large['aa'], 'aa.webp'); self.assertEqual(w.check(), [])
        self.assertEqual(self.read('photos/journeys-lg/aa.webp'), b'L')

    def test_remove_takes_the_larger_copy_with_it_and_records_why(self):
        self.full(); w = self.fresh(); w.remove('osprey', 'notfree', 'commons'); w.commit(); w = self.fresh()
        self.assertFalse(w.has('osprey') or w.has_large('osprey')); self.assertTrue(w.is_missing('osprey')); self.assertIn('commons', w.tried['osprey'])
        for rel in ('journeys', 'journeys-lg'): self.assertEqual(os.listdir(os.path.join(self.d, 'photos', rel)), [])
        self.assertEqual(w.check(), [])

    def test_a_different_picture_drops_the_old_larger_copy(self):
        self.full(); w = self.fresh(); w.put('osprey', row('https://commons.wikimedia.org/wiki/File:Y.jpg'), b'S2'); w.commit(); w = self.fresh()
        self.assertFalse(w.has_large('osprey')); self.assertEqual(w.check(), []); self.assertEqual(os.listdir(os.path.join(self.d, 'photos/journeys-lg')), [])

    def test_the_same_picture_keeps_its_larger_copy(self):
        self.full(); w = self.fresh(); w.put('osprey', row(), b'S'); w.commit(); w = self.fresh()
        self.assertTrue(w.has_large('osprey')); self.assertEqual(w.check(), []); self.assertEqual(self.read('photos/journeys-lg/osprey.webp'), b'L')

    def test_miss_refuses_a_journey_with_a_picture_and_counts_attempts(self):
        self.w.put('aa', row(), b'S')
        with self.assertRaises(ValueError): self.w.miss('aa', 'nophoto')
        with self.assertRaises(ValueError): self.w.note_tried('aa', 'commons')
        self.w.miss('bb', 'timeout', 'commons'); self.w.miss('bb', 'timeout', 'commons'); self.assertEqual(self.w.miss_['bb']['attempts'], 2)
        self.w.note_tried('cc', 'openverse'); self.assertIn('openverse', self.w.tried['cc']); self.assertFalse(self.w.is_missing('cc'))

    def test_check_finds_what_a_killed_job_leaves_and_repair_removes_it(self):
        self.full(); os.remove(os.path.join(self.d, 'photos/journeys-lg/osprey.webp'))
        with open(os.path.join(self.d, 'photos/journeys/stray.webp'), 'wb') as f: f.write(b'x')
        w = self.fresh(); self.assertEqual(len(w.check()), 2)
        w.repair(); w = self.fresh(); self.assertEqual(w.check(), []); self.assertTrue(w.has('osprey')); self.assertFalse(w.has_large('osprey'))

    def test_repair_drops_a_row_whose_file_is_gone(self):
        self.full(); os.remove(os.path.join(self.d, 'photos/journeys/osprey.webp')); w = self.fresh(); self.assertTrue(w.check())
        w.repair(); w = self.fresh(); self.assertFalse(w.has('osprey') or w.has_large('osprey')); self.assertEqual(w.check(), [])

    def test_commit_is_idempotent_and_leaves_no_temp_files(self):
        self.full(); before = {(r, f) for r, _, fs in os.walk(self.d) for f in fs}; self.fresh().commit()
        self.assertEqual({(r, f) for r, _, fs in os.walk(self.d) for f in fs}, before); self.assertFalse([f for _, f in before if f.endswith('.tmp')])

    def test_dirty_authors_are_listed(self):
        self.w.put('aa', dict(row(), a='Jane Roe'), b'S'); self.w.pics['bb'] = dict(row(), a='John (talk) 12:01, 3 May 2012', f='bb.webp')
        self.assertEqual(self.w.dirty_authors(), ['bb'])

if __name__ == '__main__': unittest.main()
