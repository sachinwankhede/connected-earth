#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import commonscategory as g

THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/X.jpg/330px-X.jpg'
OK = ('CC BY-SA 4.0', 'A. Person', 'https://creativecommons.org/licenses/by-sa/4.0', THUMB, 'image/jpeg')


class CategoryTests(unittest.TestCase):
    def test_the_category_must_be_the_place_itself(self):
        good = g.good_category
        self.assertEqual(good(['Hotels in Wisconsin', 'Mill Bluff State Park'], 'Mill Bluff State Park'), 'Mill Bluff State Park')
        self.assertEqual(good(['Castle Rock State Park (California)'], 'Castle Rock State Park', 'California, USA'), 'Castle Rock State Park (California)')
        self.assertEqual(good(['Jones-Confluence Point State Park'], 'Edward "ted" and Pat Jones-confluence Point State Park'), 'Jones-Confluence Point State Park')
        self.assertEqual(good(['Nisqually State Park'], 'Nisqually'), 'Nisqually State Park')
        self.assertIsNone(good([], 'Mill Bluff State Park')); self.assertIsNone(good(['Mill Bluff'], 'State Park'))

    def test_the_wrong_places_of_the_first_full_run_are_refused(self):
        good = g.good_category
        for name, cat in (('Baker Creek State Park', 'Baker River, Washington State'), ('Branch Lake', 'Sprague Branch of the Salt Lake City Public Library'),
                          ('Buffalo Rock State Park', 'Mount Buffalo'), ('Big Cypress State Park', 'Big Cypress National Preserve'),
                          ('Natchez State Park', 'Natchez National Historical Park'), ('Hyde Memorial State Park', 'ANZAC War Memorial (Sydney)'),
                          ('Perry State Park', 'Perry Park, Sydney'), ('Pickett', 'Pickett (surname)'), ('Riverside', 'Riverside'),
                          ('Pomona State Park', 'Pomona, California'), ('White Lake State Park', 'White Oak Lake State Park'),
                          ('Lake Greenwood State Park', 'Greenwood Lake Dam'), ('Fall River State Park', 'Fall River Heritage State Park'),
                          ('Umbagog State Park', 'Umbagog National Wildlife Refuge'), ('Miller Peninsula', 'Olympic Peninsula'),
                          ('St Marys River Sp', 'Grand Lake St. Marys'), ('Glade Creek State Park', 'Glade Creek Grist Mill')):
            self.assertIsNone(good([cat], name), (name, cat))

    def test_a_bracketed_region_must_be_the_places_own_and_word_order_must_match(self):
        good = g.good_category
        for name, cat, region in (('Castle Rock State Park', 'Castle Rock State Park (California)', 'Illinois, USA'), ('East Beach', 'East Beach (Santa Barbara, California)', 'Rhode Island, USA'),
                                  ('Sunset Lake', 'Sunset Lake (Black Sand Basin, Yellowstone National Park)', 'Delaware, USA'), ('Lewis and Clark State Park', 'Lewis and Clark State Park (Washington)', 'Missouri, USA'),
                                  ('Buck Mountain', 'Buck Mountain (Wyoming)', 'New Jersey, USA'), ('Chickasaw State Park', 'Chickasaw State Park (Tennessee)', 'Alabama, USA'),
                                  ('White Lake State Park', 'Lake White State Park', 'New Hampshire, USA'), ('Castle Rock State Park', 'Castle Rock State Park (California)', '')):
            self.assertIsNone(good([cat], name, region), (name, cat, region))
        self.assertEqual(good(['Wells State Park (Massachusetts)'], 'Wells State Park', 'Massachusetts, USA'), 'Wells State Park (Massachusetts)')

    def test_a_file_of_another_kind_of_park_and_a_title_shared_by_two_regions_are_skipped(self):
        files = ['Mount_Pisgah_County_Park_view.jpg', 'Pisgah_State_Park_trail.jpg']
        self.assertEqual(g.choose(files, g.n.words('Pisgah State Park'), {f: OK for f in files}, {'state'})[0], 'Pisgah_State_Park_trail.jpg')
        self.assertIsNone(g.choose(files[:1], g.n.words('Pisgah State Park'), {files[0]: OK}, {'state'}))

    def test_a_file_naming_the_place_comes_first_and_buildings_closed_licences_pngs_figures_and_clippings_are_refused(self):
        files = ['Sign_at_entrance.jpg', 'Random_view.jpg', 'Mill_Bluff_cliff.jpg', 'Mill_Bluff_a.png', 'Mill_Bluff_b.jpg']
        inf = {f: OK for f in files}; inf['Mill_Bluff_a.png'] = OK[:4] + ('image/png',); inf['Mill_Bluff_b.jpg'] = ('CC BY-NC 4.0',) + OK[1:]
        self.assertEqual(g.choose(files, g.n.words('Mill Bluff'), inf)[0], 'Mill_Bluff_cliff.jpg')
        self.assertEqual(g.choose(['Random_view.jpg'], g.n.words('Mill Bluff'), {'Random_view.jpg': OK})[0], 'Random_view.jpg')   # the category is the place, so a file without the word is fine
        bad = ['Sign_at_entrance.jpg', 'Mill_Hotel.jpg', 'Frog_Figure_2_(cropped).jpg', 'Natchez_Daily_Courier,_1853.jpg', 'Dian_Fossey,_bulletin-1968.jpg']
        self.assertIsNone(g.choose(bad, g.n.words('Mill Bluff'), {f: OK for f in bad}))


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

    def test_a_title_shared_by_places_in_different_regions_is_not_matched(self):
        json.dump({'id': 'cc', 'name': 'Alpha Gorge State Park', 'imgwiki': 'Alpha Gorge State Park', 'lat': 3.0, 'lon': 4.0, 'place': 'Idaho, USA'}, open('data/places/cc.json', 'w'))
        json.dump({'id': 'aa', 'name': 'Alpha Gorge State Park', 'imgwiki': 'Alpha Gorge State Park', 'lat': 1.0, 'lon': 2.0, 'place': 'New York, USA'}, open('data/places/aa.json', 'w'))
        man, miss, tried = self.run_main()
        self.assertEqual(man, {}); self.assertIn('Alpha Gorge State Park', tried)

    def test_a_failed_download_is_not_marked_tried(self):
        man, miss, tried = self.run_main(dl=None)
        self.assertEqual(man, {}); self.assertIn('Alpha Gorge State Park', miss); self.assertNotIn('Alpha Gorge State Park', tried)


if __name__ == '__main__': unittest.main()
