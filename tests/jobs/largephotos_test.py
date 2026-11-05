#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import largephotos as lp


class LargePhotosTests(unittest.TestCase):
    def test_width_is_changed_in_each_kind_of_manifest_path(self):
        self.assertEqual(lp.width_path('a/ab/Osprey.jpg/330px-Osprey.jpg', 500), 'a/ab/Osprey.jpg/500px-Osprey.jpg')
        self.assertEqual(lp.width_path('https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Osprey.jpg/330px-Osprey.jpg', 500), 'a/ab/Osprey.jpg/500px-Osprey.jpg')
        self.assertEqual(lp.width_path('https://upload.wikimedia.org/wikipedia/commons/a/ab/Osprey.jpg', 500), 'a/ab/Osprey.jpg/500px-Osprey.jpg')

    def test_ranking_counts_places_and_takes_the_title_the_page_uses(self):
        def eco(i, *nodes): return {'id': i, 'nodes': [dict(zip(('latin', 'wiki', 'canonicalWiki'), n)) for n in nodes]}
        ecos = [eco('p1', ('Pandion haliaetus', 'Osprey', None), ('Alces alces', 'Moose', None)), eco('p2', ('Pandion haliaetus', 'Osprey', None)), eco('p3', ('Pandion haliaetus', 'Osprey', None), ('Ursus arctos', 'Brown bear', None)),
                {'id': 'p4', 'nodes': [{'cat': 1, 'latin': 'Rain'}, {'latin': 'No picture', 'wiki': 'No picture'}]}]
        hosted = {'Osprey': 'a.webp', 'Moose': 'b.webp', 'Brown bear': 'c.webp'}
        self.assertEqual(lp.ranking(ecos, hosted), [('Osprey', 3), ('Brown bear', 1), ('Moose', 1)], 'most places first, then by title; no picture, no entry; resources are not species')


if __name__ == '__main__':
    unittest.main()
