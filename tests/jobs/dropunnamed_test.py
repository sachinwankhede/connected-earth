#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import dropunnamed as d

class SplitTests(unittest.TestCase):
    def test_only_rows_with_no_author_found_are_removed(self):
        rows = [dict(kind='place', key='A', **{'class': 'none'}), dict(kind='place', key='B', **{'class': 'artist'}),
                dict(kind='species', key='Z', **{'class': 'none'}), dict(kind='species', key='Y', **{'class': 'attribution'}), dict(kind='species', key='X', **{'class': 'own-work'}), dict(kind='species', key='W', **{'class': 'none'})]
        self.assertEqual(d.split(rows), (['A'], ['W', 'Z']))

if __name__ == '__main__': unittest.main()
