"""lib/journey_pics.py: the journey covers read by journey id; nothing breaks while the new files are absent (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 1)."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import journey_pics as jpics
import journey_photos as jp

def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

def root_with_journeys(*ids):
    d = tempfile.mkdtemp(); w(d, 'data/journeys/config.json', {'couple': None, 'src': None})
    for n, i in enumerate(ids): w(d, 'data/journeys/%s.json' % i, {'pos': n, 'id': i, 'title': i})
    return d

class ReaderTests(unittest.TestCase):
    def test_absent_files_give_empty_and_shape_none(self):
        d = tempfile.mkdtemp(); self.assertEqual(jpics.load(d), {'pics': {}, 'large': {}, 'missing': {}, 'shape': 'none'}); self.assertEqual(jpics.check(d), [])

    def test_the_new_shape_is_read_as_it_is(self):
        d = tempfile.mkdtemp(); x = jp.JourneyPhotos(d)
        x.put('osprey', {'a': 'X', 'l': 'CC BY 4.0', 'wiki': 'Osprey'}, b'S'); x.put_large('osprey', b'L'); x.miss('dust', 'nophoto'); x.commit()
        r = jpics.load(d); self.assertEqual(r['shape'], 'journey'); self.assertEqual(r['pics']['osprey']['f'], 'osprey.webp'); self.assertEqual(r['large'], {'osprey': 'osprey.webp'}); self.assertEqual(list(r['missing']), ['dust'])

    def test_check_passes_for_a_consistent_set_and_reports_problems(self):
        d = root_with_journeys('osprey', 'dust'); x = jp.JourneyPhotos(d); x.put('osprey', {'a': 'X', 'l': 'CC0'}, b'S'); x.commit()
        self.assertEqual(jpics.check(d), [])
        os.remove(os.path.join(d, 'photos/journeys/osprey.webp')); self.assertEqual(len(jpics.check(d)), 1)

    def test_check_reports_an_id_that_is_not_a_journey(self):
        d = root_with_journeys('osprey'); x = jp.JourneyPhotos(d); x.put('ospray', {'a': 'X', 'l': 'CC0'}, b'S'); x.miss('dust', 'nophoto'); x.commit()
        errs = jpics.check(d); self.assertEqual(len(errs), 2); self.assertTrue(all('is not a journey id' in e for e in errs))
        self.assertEqual(jpics.check(d, ids={'ospray', 'dust'}), [])

    def test_the_real_journey_ids_are_the_data_files(self):
        ids = jpics.journey_ids(os.path.join(HERE, '..', '..')); self.assertEqual(len(ids), len(set(ids))); self.assertIn('osprey', ids)

if __name__ == '__main__': unittest.main()
