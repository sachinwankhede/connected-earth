#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
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


class SpeciesBySidTests(unittest.TestCase):   # #934
    def test_fill_and_drop_go_through_the_species_writer(self):
        import json, tempfile
        from species_photos import SpeciesPhotos
        r = tempfile.mkdtemp(); os.makedirs(os.path.join(r, 'photos', 'places')); w = SpeciesPhotos(r); c = 'https://commons.wikimedia.org/wiki/File:'
        w.put('s1', {'a': 'x', 'l': 'CC BY 4.0', 'p': c + 'A.jpg', 'wiki': 'A'}, b'1'); w.put('s2', {'a': 'x', 'l': 'CC BY 4.0', 'p': c + 'B.jpg', 'wiki': 'B'}, b'2'); w.put('s3', {'a': 'Jane', 'l': 'CC BY 4.0', 'p': c + 'C.jpg', 'wiki': 'C'}, b'3')
        w.pics['s1']['a'] = 'Unknown'; w.pics['s2']['a'] = 'Unknown'; w.commit()
        self.assertEqual(d.fill(r, {'place': {}, 'species': {'s1': 'Stan', 's3': 'Zed'}}, dry=True), 1); self.assertEqual(SpeciesPhotos(r).pics['s1']['a'], 'Unknown')
        self.assertEqual(d.fill(r, {'place': {}, 'species': {'s1': 'Stan', 's3': 'Zed'}}), 1)
        w = SpeciesPhotos(r); self.assertEqual(w.pics['s1']['a'], 'Stan'); self.assertEqual(w.pics['s3']['a'], 'Jane')
        self.assertEqual([x['key'] for x in d.al.candidates({}, d.al.species_credits(r))], ['s2'])
        d.dp.drop(r, False, ['s2'], hold=True); w = SpeciesPhotos(r); self.assertEqual(sorted(w.pics), ['s1', 's3']); self.assertIn('s2', w.miss_); self.assertEqual(w.check(), [])

if __name__ == '__main__': unittest.main()
