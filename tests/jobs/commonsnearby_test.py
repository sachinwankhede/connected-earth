#!/usr/bin/env python3
import json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import commonsnearby as n

THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/X.jpg/330px-X.jpg'
OK = ('CC BY-SA 4.0', 'A. Person', 'https://creativecommons.org/licenses/by-sa/4.0', THUMB, 'image/jpeg')


class WordTests(unittest.TestCase):
    def test_generic_and_short_words_are_ignored_and_accents_folded(self):
        self.assertEqual(n.words('Cañon State Park'), {'canon'})
        self.assertEqual(n.words('Lake Of The Woods'), {'woods'})
        self.assertEqual(n.words('Ely_Lake_2019.jpg'), set())


class MatchTests(unittest.TestCase):
    def test_the_nearest_file_sharing_a_name_word_wins(self):
        cands = [('Village_church.jpg', 10), ('Tallulah_Gorge_rim.jpg', 300), ('Tallulah_Gorge_bridge.jpg', 500)]
        inf = {k: OK for k, _ in cands}
        got, dist = n.match('Tallulah Gorge State Park', 'Tallulah Gorge State Park', cands, inf)
        self.assertEqual((got[0], dist), ('Tallulah_Gorge_rim.jpg', 300))

    def test_no_name_word_in_any_file_gives_no_match(self):
        self.assertIsNone(n.match('Tallulah Gorge', 'Tallulah Gorge', [('Church.jpg', 5)], {'Church.jpg': OK}))

    def test_closed_licence_png_and_map_are_refused_even_with_the_word(self):
        cands = [('Tallulah_map.jpg', 1), ('Tallulah_a.png', 2), ('Tallulah_b.jpg', 3)]
        inf = {'Tallulah_map.jpg': OK, 'Tallulah_a.png': OK[:4] + ('image/png',), 'Tallulah_b.jpg': ('CC BY-NC 4.0',) + OK[1:]}
        self.assertIsNone(n.match('Tallulah', 'Tallulah', cands, inf))


class StricterTests(unittest.TestCase):
    def test_a_casino_sharing_one_word_is_refused(self):
        f = 'Laughlin,_Colorado_Belle_Hotel_&_Casino_(Nevada)_(1).jpg'
        self.assertIsNone(n.match('Big Bend of the Colorado State Park', 'Big Bend of the Colorado State Park', [(f, 1334)], {f: OK}))

    def test_half_of_the_distinctive_words_must_appear(self):
        f = 'Bald_Head_light.jpg'; g = 'Head_of_a_dog.jpg'
        name = 'Bald Head Island State Natural Area'   # bald, head, natural: two needed
        self.assertIsNotNone(n.match(name, name, [(f, 1)], {f: OK}))
        self.assertIsNone(n.match(name, name, [(g, 1)], {g: OK}))


class RoadAndTownTests(unittest.TestCase):
    def test_roads_towns_temples_capitols_signs_and_damage_are_refused_as_whole_words(self):
        for bad in ('2020_View_west_along_Interstate_280_at_Exit_1.jpg', 'View_north_along_Rock_Boulevard_(Nevada_State_Route_668).jpg',
                    'View_of_Lewis_and_Clark_Village_MO.jpg', 'Nauvoo_Temple01.jpg', 'Louisiana_State_Capitol_2012.jpg', 'Legion_Park_Lodge.jpg',
                    'Storm_wind_damage_at_Lake_Martin_AL.jpg', 'Sign_for_Horsethief_Butte_Trail.jpg'):
            self.assertTrue(n.BUILDING.search(bad), bad)
        for ok in ('Railroad_bridge_over_the_Blackfoot_River.jpg', 'Plantation_trail.jpg', 'Riverbank_view.jpg', 'Signal_Mountain.jpg', 'Innsbruck_Gorge.jpg',
                   'Mill_Bluff_State_Park_2012A.jpg', 'Crater_of_Diamonds_State_Park_pano.jpg'):
            self.assertFalse(n.BUILDING.search(ok), ok)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd(); self.d = tempfile.mkdtemp(); os.chdir(self.d)
        os.makedirs('photos/places'); os.makedirs('data/places')
        for i, t in (('aa', 'Alpha Gorge'), ('bb', 'Beta Hollow')):
            json.dump({'id': i, 'name': t, 'imgwiki': t, 'lat': 1.0, 'lon': 2.0}, open('data/places/%s.json' % i, 'w'))
        json.dump({t: {'status': 'nophoto'} for t in ('Alpha Gorge', 'Beta Hollow')}, open('photos/places/missing.json', 'w'))
        json.dump({}, open('photos/places/places.json', 'w'))

    def tearDown(self): os.chdir(self.old)

    def run_main(self, dl=b'JPEG'):
        near = lambda lat, lon: [('Alpha_Gorge_view.jpg', 120), ('Other.jpg', 5)]
        with mock.patch.object(sys, 'argv', ['x']), mock.patch.object(n, 'nearby', near), \
                mock.patch.object(n.cp, 'commons_info', lambda fs: {'Alpha_Gorge_view.jpg': OK}), mock.patch.object(n.wm, 'get', lambda u, raw=False: dl):
            n.main()
        load = lambda p: json.load(open(p))
        return load('photos/places/places.json'), load('photos/places/missing.json'), load('photos/places_nearby_tried.json')

    def test_a_match_is_stored_and_a_miss_is_marked_tried(self):
        man, miss, tried = self.run_main()
        self.assertEqual(man['Alpha Gorge']['f'], 'aa.jpg'); self.assertTrue(os.path.exists('photos/places/aa.jpg'))
        self.assertNotIn('Alpha Gorge', miss); self.assertIn('Beta Hollow', miss)
        self.assertIn('Beta Hollow', tried); self.assertNotIn('Alpha Gorge', tried)

    def test_a_failed_download_is_not_marked_tried(self):
        man, miss, tried = self.run_main(dl=None)
        self.assertEqual(man, {}); self.assertIn('Alpha Gorge', miss); self.assertNotIn('Alpha Gorge', tried)


if __name__ == '__main__': unittest.main()
