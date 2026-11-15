#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import dropunnamed as d

class SplitTests(unittest.TestCase):
    def test_only_rows_with_no_author_found_are_removed(self):
        rows = [dict(kind='place', key='A', **{'class': 'none'}), dict(kind='place', key='B', **{'class': 'artist'}),
                dict(kind='species', key='Z', **{'class': 'none'}), dict(kind='species', key='Y', **{'class': 'attribution'}), dict(kind='species', key='X', **{'class': 'own-work'}), dict(kind='species', key='W', **{'class': 'none'})]
        self.assertEqual(d.split(rows), (['A'], ['W', 'Z']))

class FillTests(unittest.TestCase):
    def test_a_found_name_replaces_only_an_unknown_author(self):
        import json, tempfile
        r = tempfile.mkdtemp(); os.makedirs(os.path.join(r, 'photos', 'places'))
        json.dump({'P': {'a': 'Unknown author', 'l': 'CC BY 4.0'}, 'Q': {'a': 'Jane Doe', 'l': 'CC BY 4.0'}}, open(os.path.join(r, 'photos/places/places.json'), 'w'))
        json.dump({'S': {'a': 'Unknown', 'l': 'CC BY-SA 3.0'}}, open(os.path.join(r, 'photos/species_metadata.json'), 'w'))
        rows = [dict(kind='place', key='P', name='Ann', **{'class': 'artist'}), dict(kind='place', key='Q', name='Zed', **{'class': 'artist'}), dict(kind='species', key='S', name='Stan Shebs', **{'class': 'attribution'}), dict(kind='species', key='N', name='', **{'class': 'none'})]
        self.assertEqual(d.fills(rows), {'place': {'P': 'Ann', 'Q': 'Zed'}, 'species': {'S': 'Stan Shebs'}})
        self.assertEqual(d.fill(r, d.fills(rows), dry=True), 2); self.assertEqual(json.load(open(os.path.join(r, 'photos/places/places.json')))['P']['a'], 'Unknown author')
        self.assertEqual(d.fill(r, d.fills(rows)), 2)
        self.assertEqual(json.load(open(os.path.join(r, 'photos/places/places.json')))['P']['a'], 'Ann'); self.assertEqual(json.load(open(os.path.join(r, 'photos/places/places.json')))['Q']['a'], 'Jane Doe')
        self.assertEqual(json.load(open(os.path.join(r, 'photos/species_metadata.json')))['S']['a'], 'Stan Shebs')

if __name__ == '__main__': unittest.main()
