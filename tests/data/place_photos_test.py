"""lib/place_photos.py: the one writer for place pictures keeps file, list entry, larger copy and missing record in step (docs/DATA-PLAN.md, steps 3 and 4)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import place_photos as pp
import photo_registry as pr

def row(sha='aa'): return {'a': 'Someone', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'sha256': sha}

class WriterTests(unittest.TestCase):
    def setUp(self): self.d = tempfile.mkdtemp(); self.w = pp.PlacePhotos(self.d)
    def fresh(self): return pp.PlacePhotos(self.d)
    def read(self, rel):
        with open(os.path.join(self.d, rel), 'rb') as f: return f.read()

    def test_put_writes_file_and_row_and_clears_the_miss(self):
        self.w.miss('okarrowhead', 'nophoto', 'nearby'); self.w.commit()
        w = self.fresh(); self.assertTrue(w.is_missing('okarrowhead'))
        w.put('okarrowhead', row(), b'JPEG'); w.commit()
        w = self.fresh()
        self.assertTrue(w.has('okarrowhead')); self.assertFalse(w.is_missing('okarrowhead')); self.assertNotIn('okarrowhead', w.tried)
        self.assertEqual(w.pics['okarrowhead']['f'], 'okarrowhead.jpg'); self.assertEqual(self.read('photos/places/okarrowhead.jpg'), b'JPEG')
        self.assertEqual(w.check(), [])

    def test_the_file_name_is_always_the_place_id(self):
        self.w.put('aa', dict(row(), f='someone-elses.jpg'), b'J'); self.w.commit()
        self.assertEqual(self.fresh().pics['aa']['f'], 'aa.jpg'); self.assertEqual(self.fresh().check(), [])

    def test_a_larger_copy_needs_a_stored_picture(self):
        with self.assertRaises(ValueError): self.w.put_large('aa', b'W')
        self.w.put('aa', row(), b'J'); self.w.put_large('aa', b'W'); self.w.commit()
        w = self.fresh(); self.assertTrue(w.has_large('aa')); self.assertEqual(w.large['aa'], 'aa.webp'); self.assertEqual(w.check(), [])

    def test_remove_takes_the_larger_copy_with_it_and_records_why(self):
        # the Arrowhead failure (#876, #880): the job removed a picture and left the larger copy behind
        self.w.put('okarrowhead', row(), b'J'); self.w.put_large('okarrowhead', b'W'); self.w.commit()
        w = self.fresh(); w.remove('okarrowhead', 'notphoto', 'photos'); w.commit()
        w = self.fresh()
        self.assertFalse(w.has('okarrowhead')); self.assertFalse(w.has_large('okarrowhead')); self.assertEqual(w.miss_['okarrowhead']['status'], 'notphoto')
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/places/okarrowhead.jpg'))); self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/places-lg/okarrowhead.webp')))
        self.assertEqual(w.check(), []); self.assertIn('photos', w.tried['okarrowhead'])

    def test_a_different_picture_drops_the_old_larger_copy_and_the_same_one_keeps_it(self):
        self.w.put('aa', row('s1'), b'J1'); self.w.put_large('aa', b'W'); self.w.commit()
        w = self.fresh(); w.put('aa', row('s1'), b'J1'); w.commit(); self.assertTrue(self.fresh().has_large('aa'))
        w = self.fresh(); w.put('aa', row('s2'), b'J2'); w.commit(); w = self.fresh()
        self.assertFalse(w.has_large('aa')); self.assertEqual(w.check(), []); self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/places-lg/aa.webp')))

    def test_a_place_with_a_picture_cannot_be_marked_missing_without_remove(self):
        self.w.put('aa', row(), b'J')
        with self.assertRaises(ValueError): self.w.miss('aa', 'nophoto')

    def test_one_retry_policy_for_every_source(self):
        t = pr._utcnow()
        self.w.miss('aa', 'nophoto', 'nearby', now=t); self.w.miss('bb', 'nophoto', 'category', now=t)
        self.assertEqual(self.w.miss_['aa']['expiresAt'], self.w.miss_['bb']['expiresAt']); self.assertEqual(self.w.miss_['aa'], pr.negative_entry('nophoto', 1, t))
        self.w.miss('aa', 'nophoto', 'category', now=t); self.assertEqual(self.w.miss_['aa']['attempts'], 2); self.assertEqual(sorted(self.w.tried['aa']), ['category', 'nearby'])

    def test_note_tried_writes_only_the_ledger(self):
        self.w.miss('aa', 'nophoto', 'wikipedia'); self.w.commit(); before = self.fresh().miss_['aa']
        w = self.fresh(); w.note_tried('aa', 'commons'); w.commit(); w = self.fresh()
        self.assertEqual(w.miss_['aa'], before, 'the missing record is untouched'); self.assertEqual(sorted(w.tried['aa']), ['commons', 'wikipedia'])
        w.put('aa', row(), b'J')
        with self.assertRaises(ValueError): w.note_tried('aa', 'nearby')

    def test_nothing_is_written_before_commit(self):
        self.w.put('aa', row(), b'J')
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/places/aa.jpg'))); self.assertFalse(os.path.exists(os.path.join(self.d, 'photos/places/places.json')))

    def test_a_job_killed_between_files_and_lists_leaves_only_an_unlisted_file_that_repair_removes(self):
        self.w.put('aa', row(), b'J'); self.w.commit()
        w = self.fresh(); w.put('bb', row(), b'J2')
        for path, data in w._write.items(): pp._write_bytes(path, data)   # the files are written, the job dies before the lists
        w = self.fresh(); errs = w.check()
        self.assertEqual(errs, ['photos/places/bb.jpg is not listed in places.json'])   # never a list row without its file
        self.assertEqual(w.repair(), ['photos/places/bb.jpg']); self.assertEqual(self.fresh().check(), [])

    def test_check_finds_what_the_validator_must_catch(self):
        self.w.put('aa', row(), b'J'); self.w.put_large('aa', b'W'); self.w.commit()
        os.remove(os.path.join(self.d, 'photos/places/aa.jpg'))
        pp._write_bytes(os.path.join(self.d, 'photos/places/congo.jpg'), b'x'); pp._write_bytes(os.path.join(self.d, 'photos/places-lg/zz.webp'), b'x')
        errs = self.fresh().check()
        self.assertEqual(len(errs), 3, errs); self.assertTrue(any('aa.jpg is missing' in e for e in errs)); self.assertTrue(any('congo.jpg is not listed' in e for e in errs)); self.assertTrue(any('zz.webp is not listed' in e for e in errs))


class RekeyTests(unittest.TestCase):
    def test_a_title_used_by_two_places_is_not_copied_and_titles_become_a_field(self):
        old = {'Alpha Park': row('a'), 'Harriman State Park': row('h'), 'Orphan title': row('o')}
        ids = {'Alpha Park': ['alpha'], 'Harriman State Park': ['nyharriman', 'idharriman']}
        new, shared, unplaced = pp.rekey(old, ids)
        self.assertEqual(sorted(new), ['alpha']); self.assertEqual(new['alpha']['wiki'], 'Alpha Park')
        self.assertEqual(shared, {'Harriman State Park': ['idharriman', 'nyharriman']}); self.assertEqual(unplaced, ['Orphan title'])


if __name__ == '__main__': unittest.main()
