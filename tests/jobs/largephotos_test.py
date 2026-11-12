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

    def test_each_source_has_its_own_download_link(self):
        self.assertEqual(lp.source_urls('openverse/abc-1'), ['https://api.openverse.org/v1/images/abc-1/thumb/'])
        self.assertEqual(lp.source_urls('inaturalist/123'), ['https://inaturalist-open-data.s3.amazonaws.com/photos/123/medium.jpg'])
        self.assertEqual(lp.source_urls('gbif/99'), [])
        c = lp.source_urls('a/ab/Osprey.jpg/330px-Osprey.jpg')
        self.assertEqual(len(c), 2); self.assertIn('500px-Osprey.jpg', c[0])

    def test_one_download_makes_both_sizes_no_larger_than_asked(self):
        from PIL import Image
        im = Image.new('RGB', (500, 333), (30, 120, 60))
        big, bs = lp.shrink(im, lp.SIZE); small, ss = lp.shrink(im, lp.SIZE_MD)
        self.assertEqual((bs, ss), ((400, 266), (192, 128)))
        self.assertLess(len(small), len(big)); self.assertEqual(im.size, (500, 333), 'the download is not changed')

    def test_ranking_counts_places_and_takes_the_title_the_page_uses(self):
        def eco(i, *nodes): return {'id': i, 'nodes': [dict(zip(('latin', 'wiki', 'canonicalWiki'), n)) for n in nodes]}
        ecos = [eco('p1', ('Pandion haliaetus', 'Osprey', None), ('Alces alces', 'Moose', None)), eco('p2', ('Pandion haliaetus', 'Osprey', None)), eco('p3', ('Pandion haliaetus', 'Osprey', None), ('Ursus arctos', 'Brown bear', None)),
                {'id': 'p4', 'nodes': [{'cat': 1, 'latin': 'Rain'}, {'latin': 'No picture', 'wiki': 'No picture'}]}]
        hosted = {'Osprey': 'a.webp', 'Moose': 'b.webp', 'Brown bear': 'c.webp'}
        self.assertEqual(lp.ranking(ecos, hosted), [('Osprey', 3), ('Brown bear', 1), ('Moose', 1)], 'most places first, then by title; no picture, no entry; resources are not species')


if __name__ == '__main__':
    unittest.main()
