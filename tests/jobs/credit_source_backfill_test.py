#!/usr/bin/env python3
import os, sys, unittest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import credit_source_backfill as C


class Backfill(unittest.TestCase):
    def test_gbif_and_openverse_pages_are_named(self):
        self.assertEqual(C.source_of('https://www.gbif.org/occurrence/123'), 'GBIF')
        self.assertEqual(C.source_of('https://openverse.org/image/2d38db67-5d58-44fa-b3cb-47c58c10709a'), 'Openverse')

    def test_commons_and_anything_else_is_not_named(self):
        for p in ('https://commons.wikimedia.org/wiki/File:A.jpg', '', None, 'not a link', 'https://evil.example/www.gbif.org', 'https://www.gbif.org.evil.example/x', 'http://www.gbif.org/x'):
            self.assertEqual(C.source_of(p), '', repr(p))

    def test_backfill_adds_s_once_and_leaves_others(self):
        m = {'A': {'p': 'https://www.gbif.org/occurrence/1'}, 'B': {'p': 'https://commons.wikimedia.org/wiki/File:B.jpg'}, 'C': {'p': 'https://www.inaturalist.org/photos/9', 's': 'iNaturalist'}, 'D': {'p': 'https://openverse.org/image/x', 's': 'Openverse'}}
        self.assertEqual(C.backfill(m), 1)
        self.assertEqual(m['A']['s'], 'GBIF'); self.assertNotIn('s', m['B']); self.assertEqual(m['C']['s'], 'iNaturalist')
        self.assertEqual(C.backfill(m), 0)


if __name__ == '__main__':
    unittest.main()
