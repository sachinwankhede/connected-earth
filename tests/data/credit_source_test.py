#!/usr/bin/env python3
"""The source name on a species picture credit (#511): the build writes it, the app shows it, Commons is the default."""
import os, sys, unittest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B


class CreditSource(unittest.TestCase):
    def test_gbif_and_openverse_are_named(self):
        self.assertEqual(B.credit_source('https://www.gbif.org/occurrence/123'), 'GBIF')
        self.assertEqual(B.credit_source('https://openverse.org/image/2d38db67-5d58-44fa-b3cb-47c58c10709a'), 'Openverse')

    def test_commons_and_anything_else_has_no_name_so_the_app_default_applies(self):
        for p in ('https://commons.wikimedia.org/wiki/File:A.jpg', '', None, 'not a link', 'https://evil.example/www.gbif.org', 'https://www.gbif.org.evil.example/x'):
            self.assertEqual(B.credit_source(p), '', repr(p))


if __name__ == '__main__':
    unittest.main()
