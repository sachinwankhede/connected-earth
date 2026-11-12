#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import commonsplacephotos as c

THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Lake.jpg/330px-Lake.jpg'


def info(**kw):
    base = {'Lake.jpg': ('CC BY-SA 4.0', 'A. Person', 'https://creativecommons.org/licenses/by-sa/4.0', THUMB, 'image/jpeg')}
    base.update(kw)
    return base


class PickTests(unittest.TestCase):
    def test_an_open_licence_jpeg_is_kept(self):
        got = c.pick(['Lake.jpg'], info())
        self.assertEqual(got[0], 'Lake.jpg'); self.assertEqual(got[1], 'CC BY-SA 4.0'); self.assertEqual(got[4], THUMB)

    def test_closed_licence_png_map_and_other_hosts_are_refused(self):
        self.assertIsNone(c.pick(['Lake.jpg'], info(**{'Lake.jpg': ('CC BY-NC 4.0', 'A', '', THUMB, 'image/jpeg')})))
        self.assertIsNone(c.pick(['Lake.jpg'], info(**{'Lake.jpg': ('CC0', 'A', '', THUMB, 'image/png')})))
        self.assertIsNone(c.pick(['Locator map of X.jpg'], {'Locator_map_of_X.jpg': ('CC0', 'A', '', THUMB, 'image/jpeg')}))
        self.assertIsNone(c.pick(['Lake.jpg'], info(**{'Lake.jpg': ('CC0', 'A', '', 'https://example.com/a.jpg', 'image/jpeg')})))
        self.assertIsNone(c.pick([], {}))

    def test_a_place_called_arrowhead_is_not_refused_but_logos_and_maps_still_are(self):
        self.assertIn('arrowhead', c.pp.NOTPHOTO.pattern, 'photos.py keeps its own filter')
        self.assertIsNone(c.NOTPHOTO.search('Arrowhead State Park.jpg'))
        for bad in ('NPS arrowhead logo.jpg', 'Arrowhead.svg', 'Locator map of Arrowhead.jpg', 'Coat of arms.jpg'):
            self.assertTrue(c.NOTPHOTO.search(bad), bad)
        got = c.pick(['Arrowhead State Park.jpg'], {'Arrowhead_State_Park.jpg': ('CC BY 4.0', 'A', '', THUMB, 'image/jpeg')})
        self.assertEqual(got[0], 'Arrowhead_State_Park.jpg')

    def test_the_second_file_is_tried_when_the_first_is_not_usable(self):
        both = info(**{'Bad.png': ('CC0', 'A', '', THUMB, 'image/png')})
        self.assertEqual(c.pick(['Bad.png', 'Lake.jpg'], both)[0], 'Lake.jpg')
        self.assertIsNone(c.pick(['Bad.png', 'X.jpg', 'Lake.jpg'], both), 'only the first two are looked at')


class EntryTests(unittest.TestCase):
    def test_the_row_has_the_keys_photos_py_writes(self):
        e = c.entry('flatheadlake', 'Flathead Lake', ('Lake.jpg', 'CC BY 4.0', 'A. Person', 'https://creativecommons.org/licenses/by/4.0', THUMB), 'now')
        self.assertEqual(sorted(e), sorted(['f', 'a', 'l', 'lu', 'p', 'w', 'checkedAt', 'fetchedAt']))
        self.assertEqual(e['f'], 'flatheadlake.jpg')
        self.assertEqual(e['p'], 'https://commons.wikimedia.org/wiki/File:Lake.jpg')
        self.assertEqual(e['w'], 'https://en.wikipedia.org/wiki/Flathead_Lake')


class RunTests(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd(); self.d = tempfile.mkdtemp(); os.chdir(self.d)
        os.makedirs('photos/places'); os.makedirs('data/places')
        for i, t in (('aa', 'Alpha Lake'), ('bb', 'Beta Park'), ('cc', 'Gamma Pass'), ('dd', 'Alpha Lake')):
            json.dump({'id': i, 'imgwiki': t}, open('data/places/%s.json' % i, 'w'))
        json.dump({'x': 1}, open('data/places/order.json', 'w'))
        json.dump({t: {'status': 'nophoto'} for t in ('Alpha Lake', 'Beta Park', 'Gamma Pass')}, open('photos/places/missing.json', 'w'))
        json.dump({}, open('photos/places/places.json', 'w'))

    def tearDown(self): os.chdir(self.old)

    def run_main(self, dl=b'JPEG'):
        names = {'Alpha Lake': ['Lake.jpg'], 'Beta Park': ['Closed.jpg']}
        inf = info(**{'Closed.jpg': ('CC BY-NC 4.0', 'A', '', THUMB, 'image/jpeg')})
        with mock.patch.object(sys, 'argv', ['x']), mock.patch.object(c.cp, 'resolve', lambda ts: {t: t for t in ts}), \
                mock.patch.object(c.cp, 'wikidata_images', lambda ts: {t: names[t] for t in ts if t in names}), \
                mock.patch.object(c.cp, 'commons_info', lambda fs: inf), mock.patch.object(c.wm, 'get', lambda u, raw=False: dl):
            c.main()
        load = lambda p: json.load(open(p))
        return load('photos/places/places.json'), load('photos/places/missing.json'), load('photos/places_commons_tried.json')

    def test_a_found_picture_is_stored_under_the_first_place_and_leaves_missing(self):
        man, miss, tried = self.run_main()
        self.assertEqual(man['Alpha Lake']['f'], 'aa.jpg')
        self.assertEqual(open('photos/places/aa.jpg', 'rb').read(), b'JPEG')
        self.assertNotIn('Alpha Lake', miss); self.assertNotIn('Alpha Lake', tried)
        self.assertFalse(os.path.exists('photos/places/dd.jpg'), 'one file per title')

    def test_titles_with_nothing_usable_stay_missing_and_are_dated(self):
        man, miss, tried = self.run_main()
        for t in ('Beta Park', 'Gamma Pass'):
            self.assertIn(t, miss); self.assertIn(t, tried); self.assertNotIn(t, man)

    def test_a_failed_download_is_not_marked_tried(self):
        man, miss, tried = self.run_main(dl=None)
        self.assertNotIn('Alpha Lake', man); self.assertIn('Alpha Lake', miss); self.assertNotIn('Alpha Lake', tried)
        self.assertFalse(os.path.exists('photos/places/aa.jpg'))


if __name__ == '__main__':
    unittest.main()
