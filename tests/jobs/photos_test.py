#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import photos as p


class PlaceTitleTests(unittest.TestCase):
    def test_a_plain_name_is_tried_as_it_is(self):
        self.assertEqual(p.titles('Gulf Islands National Seashore'), ['Gulf Islands National Seashore'])

    def test_a_combined_name_adds_only_parts_that_name_a_park(self):
        self.assertEqual(p.titles('Flathead Lake/Big Arm State Park'), ['Flathead Lake/Big Arm State Park', 'Big Arm State Park'])
        self.assertEqual(p.titles('Hobbs State Park / Conservation Management Area'), ['Hobbs State Park / Conservation Management Area', 'Hobbs State Park'])
        self.assertEqual(p.titles('Okmulgee/dripping State Park'), ['Okmulgee/dripping State Park', 'dripping State Park'], 'a bare town name is not tried')
        self.assertEqual(p.titles('Hoko River / Cowan Ranch'), ['Hoko River / Cowan Ranch'], 'no park word, nothing added')

    def test_the_slash_is_encoded_in_the_summary_request(self):
        seen = []
        with mock.patch.object(p, 'get', lambda u, raw=False: seen.append(u) or None):
            p.fetch('x', 'A/B State Park', tempfile.mkdtemp(), {}, 'A/B State Park')
        self.assertTrue(seen[0].endswith('/A%2FB_State_Park'), seen[0])

    def test_a_part_that_works_is_stored_under_the_places_own_title(self):
        calls = []
        def fake(i, t, out, man, key):
            calls.append(t)
            if t == 'Big Arm State Park': man[key] = {'f': i + '.jpg'}; return 'ok'
            return 'nophoto'
        man = {}
        with mock.patch.object(p, 'fetch', fake):
            self.assertEqual(p.one('mtx', 'Flathead Lake/Big Arm State Park', '.', man), 'ok')
        self.assertEqual(calls, ['Flathead Lake/Big Arm State Park', 'Big Arm State Park'])
        self.assertIn('Flathead Lake/Big Arm State Park', man)

    def test_a_transient_problem_beats_a_permanent_no_photo(self):
        with mock.patch.object(p, 'fetch', lambda i, t, out, man, key: 'nophoto' if t == 'A/B State Park' else 'nodl'):
            self.assertEqual(p.one('x', 'A/B State Park', '.', {}), 'nodl')
        with mock.patch.object(p, 'fetch', lambda *a: 'nophoto'):
            self.assertEqual(p.one('x', 'A/B State Park', '.', {}), 'nophoto')


if __name__ == '__main__':
    unittest.main()
