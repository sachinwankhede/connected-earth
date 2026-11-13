#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import commonscategory as g

THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/X.jpg/330px-X.jpg'
OK = ('CC BY-SA 4.0', 'A. Person', 'https://creativecommons.org/licenses/by-sa/4.0', THUMB, 'image/jpeg')


class CategoryTests(unittest.TestCase):
    def test_a_category_must_share_half_of_the_distinctive_words_and_name_no_building(self):
        want = g.n.words('Mill Bluff State Park')   # mill, bluff: one needed
        self.assertEqual(g.good_category(['Hotels in Wisconsin', 'Mill Bluff State Park'], want), 'Mill Bluff State Park')
        self.assertIsNone(g.good_category(['Wisconsin state parks', 'Mill Hotel'], want))
        self.assertIsNone(g.good_category([], want))
        self.assertIsNone(g.good_category(['Mill Bluff'], set()))

    def test_a_file_naming_the_place_comes_first_and_buildings_closed_licences_and_pngs_are_refused(self):
        files = ['Sign_at_entrance.jpg', 'Random_view.jpg', 'Mill_Bluff_cliff.jpg', 'Mill_Bluff_a.png', 'Mill_Bluff_b.jpg']
        inf = {f: OK for f in files}; inf['Mill_Bluff_a.png'] = OK[:4] + ('image/png',); inf['Mill_Bluff_b.jpg'] = ('CC BY-NC 4.0',) + OK[1:]
        self.assertEqual(g.choose(files, g.n.words('Mill Bluff'), inf)[0], 'Mill_Bluff_cliff.jpg')
        self.assertEqual(g.choose(['Random_view.jpg'], g.n.words('Mill Bluff'), {'Random_view.jpg': OK})[0], 'Random_view.jpg')   # the category is the place, so a file without the word is fine
        self.assertIsNone(g.choose(['Sign_at_entrance.jpg', 'Mill_Hotel.jpg'], g.n.words('Mill Bluff'), {f: OK for f in ('Sign_at_entrance.jpg', 'Mill_Hotel.jpg')}))


class RunTests(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd(); self.d = tempfile.mkdtemp(); os.chdir(self.d)
        os.makedirs('photos/places'); os.makedirs('data/places')
        for i, t in (('aa', 'Alpha Gorge State Park'), ('bb', 'Beta Hollow State Park')):
            json.dump({'id': i, 'name': t, 'imgwiki': t, 'lat': 1.0, 'lon': 2.0}, open('data/places/%s.json' % i, 'w'))
        json.dump({t: {'status': 'nophoto'} for t in ('Alpha Gorge State Park', 'Beta Hollow State Park')}, open('photos/places/missing.json', 'w'))
        json.dump({}, open('photos/places/places.json', 'w'))

    def tearDown(self): os.chdir(self.old)

    def run_main(self, dl=b'JPEG'):
        cats = lambda name: ['Alpha Gorge State Park'] if name.startswith('Alpha') else ['Wisconsin state parks']
        with mock.patch.object(sys, 'argv', ['x']), mock.patch.object(g, 'categories', cats), mock.patch.object(g, 'category_files', lambda cat: ['Alpha_Gorge_view.jpg']), \
                mock.patch.object(g.cp, 'commons_info', lambda fs: {'Alpha_Gorge_view.jpg': OK}), mock.patch.object(g.wm, 'get', lambda u, raw=False: dl):
            g.main()
        load = lambda p: json.load(open(p))
        return load('photos/places/places.json'), load('photos/places/missing.json'), load('photos/places_category_tried.json')

    def test_a_match_is_stored_and_a_miss_is_marked_tried_in_its_own_file(self):
        man, miss, tried = self.run_main()
        self.assertEqual(man['Alpha Gorge State Park']['f'], 'aa.jpg'); self.assertTrue(os.path.exists('photos/places/aa.jpg'))
        self.assertNotIn('Alpha Gorge State Park', miss); self.assertIn('Beta Hollow State Park', miss)
        self.assertIn('Beta Hollow State Park', tried); self.assertFalse(os.path.exists('photos/places_nearby_tried.json'))

    def test_a_failed_download_is_not_marked_tried(self):
        man, miss, tried = self.run_main(dl=None)
        self.assertEqual(man, {}); self.assertIn('Alpha Gorge State Park', miss); self.assertNotIn('Alpha Gorge State Park', tried)


if __name__ == '__main__': unittest.main()
