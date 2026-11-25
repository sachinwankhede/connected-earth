"""lib/species_photos.py: the one writer for species pictures keeps the three copies, the list rows and the missing record in step (docs/DATA-PLAN.md, "Species pictures"; #934)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import species_photos as sp

def row(p='https://commons.wikimedia.org/wiki/File:X.jpg'): return {'a': 'Someone', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': p, 'wiki': 'Podocarpus'}

class WriterTests(unittest.TestCase):
    def setUp(self): self.d = tempfile.mkdtemp(); self.w = sp.SpeciesPhotos(self.d)
    def fresh(self): return sp.SpeciesPhotos(self.d)
    def read(self, rel):
        with open(os.path.join(self.d, rel), 'rb') as f: return f.read()
    def full(self, sid='podocarpus'):
        self.w.put(sid, row(), b'S'); self.w.put_medium(sid, b'M'); self.w.put_large(sid, b'L'); self.w.commit()

    def test_put_refuses_any_licence_with_no_named_author(self):
        for a in ('', 'Unknown author', 'unknown', 'Anonymous'):
            with self.assertRaises(ValueError): self.w.put('s1', dict(row(), a=a), b'x')
        self.assertFalse(self.w.has('s1'))
        with self.assertRaises(ValueError): self.w.put('s1', dict(row(), a='Unknown author', l='CC0'), b'x')   # every licence needs a named author (owner, 25 Nov, #887)
        self.assertFalse(self.w.has('s1'))
        self.w.put('s1', dict(row(), a='Jane Roe', l='CC0'), b'x'); self.assertTrue(self.w.has('s1'))

    def test_put_writes_file_and_row_and_clears_the_miss(self):
        self.w.miss('abies-alba', 'nophoto', 'commons'); self.w.commit()
        w = self.fresh(); self.assertTrue(w.is_missing('abies-alba'))
        w.put('abies-alba', row(), b'WEBP'); w.commit(); w = self.fresh()
        self.assertTrue(w.has('abies-alba')); self.assertFalse(w.is_missing('abies-alba')); self.assertNotIn('abies-alba', w.tried)
        f = w.pics['abies-alba']['f']; self.assertEqual(self.read('photos/species-md/' + f), b'WEBP'); self.assertEqual(w.medium['abies-alba'], f); self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/species'))); self.assertEqual(w.check(), [])   # the 192 px picture is the stored one (#1188)

    def test_two_species_sharing_a_title_each_get_their_own_row(self):
        self.w.put('podocarpus', row(), b'A'); self.w.put('podocarpus-urbanii', row(p='https://commons.wikimedia.org/wiki/File:Z.jpg'), b'B'); self.w.commit(); w = self.fresh()
        self.assertEqual(w.pics['podocarpus']['wiki'], w.pics['podocarpus-urbanii']['wiki']); self.assertNotEqual(w.pics['podocarpus']['f'], w.pics['podocarpus-urbanii']['f'])
        self.assertEqual(w.check(), []); w.remove('podocarpus', 'notfree'); w.commit(); w = self.fresh()
        self.assertTrue(w.has('podocarpus-urbanii')); self.assertFalse(w.has('podocarpus')); self.assertEqual(w.check(), [])

    def test_species_showing_the_same_picture_share_one_file_until_the_last_one_goes(self):
        for sid in ('rain', 'rainfall'): self.w.put(sid, row(), b'SAME'); self.w.put_medium(sid, b'M'); self.w.put_large(sid, b'L')
        self.w.commit(); w = self.fresh(); f = w.pics['rain']['f']; self.assertEqual(f, w.pics['rainfall']['f'])
        self.assertEqual(len(os.listdir(os.path.join(self.d, 'photos/species-md'))), 1); self.assertEqual(w.check(), [])
        w.remove('rain', 'notfree'); w.commit(); w = self.fresh(); self.assertEqual(w.check(), []); self.assertTrue(os.path.exists(os.path.join(self.d, 'photos/species-lg', f)))
        w.remove('rainfall', 'notfree'); w.commit(); self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/species-lg', f))); self.assertEqual(self.fresh().check(), [])

    def test_a_copy_needs_a_stored_picture(self):
        for fn in (self.w.put_medium, self.w.put_large):
            with self.assertRaises(ValueError): fn('aa', b'W')
        self.full('aa'); w = self.fresh()
        self.assertTrue(w.has_medium('aa') and w.has_large('aa')); self.assertEqual(w.large['aa'], w.pics['aa']['f']); self.assertEqual(w.check(), [])

    def test_remove_takes_both_copies_with_it_and_records_why(self):
        self.full(); w = self.fresh(); w.remove('podocarpus', 'notfree', 'commons'); w.commit(); w = self.fresh()
        self.assertFalse(w.has('podocarpus') or w.has_medium('podocarpus') or w.has_large('podocarpus')); self.assertTrue(w.is_missing('podocarpus'))
        for rel in ('species-md', 'species-lg'): self.assertEqual(os.listdir(os.path.join(self.d, 'photos', rel)), [])
        self.assertEqual(w.check(), [])

    def test_a_different_picture_drops_the_old_copies(self):
        self.full(); w = self.fresh(); w.put('podocarpus', row('https://commons.wikimedia.org/wiki/File:Y.jpg'), b'S2'); w.commit(); w = self.fresh()
        self.assertFalse(w.has_large('podocarpus')); self.assertEqual(w.medium['podocarpus'], w.pics['podocarpus']['f'], 'the new 192 px picture is its own medium copy'); self.assertEqual(w.check(), []); self.assertEqual(len(os.listdir(os.path.join(self.d, 'photos/species-lg'))), 0); self.assertEqual(len(os.listdir(os.path.join(self.d, 'photos/species-md'))), 1)

    def test_the_same_picture_keeps_its_copies(self):
        self.full(); w = self.fresh(); w.put('podocarpus', row(), b'S'); w.commit(); w = self.fresh()
        self.assertTrue(w.has_medium('podocarpus') and w.has_large('podocarpus')); self.assertEqual(w.check(), [])

    def test_miss_refuses_a_species_with_a_picture_and_counts_attempts(self):
        self.w.put('aa', row(), b'S')
        with self.assertRaises(ValueError): self.w.miss('aa', 'nophoto')
        self.w.miss('bb', 'timeout', 'commons'); self.w.miss('bb', 'timeout', 'commons'); self.assertEqual(self.w.miss_['bb']['attempts'], 2)
        self.w.note_tried('cc', 'openverse'); self.assertIn('openverse', self.w.tried['cc']); self.assertFalse(self.w.is_missing('cc'))

    def test_check_finds_what_a_killed_job_leaves_and_repair_removes_it(self):
        self.full(); f = self.fresh().pics['podocarpus']['f']; os.remove(os.path.join(self.d, 'photos/species-lg', f))
        os.makedirs(os.path.join(self.d, 'photos/species'), exist_ok=True)
        with open(os.path.join(self.d, 'photos/species/stray.webp'), 'wb') as f: f.write(b'x')
        w = self.fresh(); self.assertEqual(len(w.check()), 2)
        w.repair(); w = self.fresh(); self.assertEqual(w.check(), []); self.assertTrue(w.has('podocarpus')); self.assertFalse(w.has_large('podocarpus'))

    def test_commit_is_idempotent_and_leaves_no_temp_files(self):
        self.full(); before = {(r, f) for r, _, fs in os.walk(self.d) for f in fs}; w = self.fresh(); w.commit()
        self.assertEqual({(r, f) for r, _, fs in os.walk(self.d) for f in fs}, before); self.assertFalse([f for _, f in before if f.endswith('.tmp')])

    def test_dirty_authors_are_listed(self):
        self.w.put('aa', dict(row(), a='Jane Roe'), b'S'); self.w.pics['bb'] = dict(row(), a='John (talk) 12:01, 3 May 2012', f='bb.webp')
        self.assertEqual(self.w.dirty_authors(), ['bb'])

if __name__ == '__main__': unittest.main()
