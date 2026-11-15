import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import cleanauthors as c
from place_photos import PlacePhotos

def row(a, l='CC BY-SA 3.0'): return {'a': a, 'l': l, 'lu': 'u', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'sha256': a[:6]}

class CleanRowsTests(unittest.TestCase):
    def test_cleans_the_dirty_rows_and_leaves_the_rest(self):
        d = tempfile.mkdtemp(); w = PlacePhotos(d)
        w.put('a', row('Ann Lee'), b'x'); w.put('b', row('Elf'), b'x'); w.pics['b']['a'] = 'The original uploader was Elf at English Wikipedia.'   # put() would already clean it: an old stored row is written directly
        w.pics['c'] = dict(row('x@y.com'), f='c.jpg'); w._write[os.path.join(d, 'photos', 'places', 'c.jpg')] = b'x'
        w.pics['d'] = dict(row('x@y.com', 'Public domain'), f='d.jpg'); w._write[os.path.join(d, 'photos', 'places', 'd.jpg')] = b'x'; w.commit()
        w = PlacePhotos(d); dry, needs0 = c.clean_rows(w, dry=True); self.assertEqual([x[0] for x in dry], ['b', 'd']); self.assertEqual(PlacePhotos(d).pics['b']['a'], 'The original uploader was Elf at English Wikipedia.')
        cleaned, needs = c.clean_rows(w); self.assertEqual(needs, ['c'])
        w2 = PlacePhotos(d); self.assertEqual(w2.pics['b']['a'], 'Elf'); self.assertEqual(w2.pics['d']['a'], 'Unknown author'); self.assertEqual(w2.pics['c']['a'], 'x@y.com'); self.assertEqual(w2.pics['a']['a'], 'Ann Lee')
        self.assertEqual(w2.dirty_authors(), ['c'])

def srow(a, l='CC BY-SA 3.0'): return {'a': a, 'l': l, 'lu': 'u', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'wiki': 'X'}

class SpeciesTests(unittest.TestCase):
    def test_cleans_species_by_sid_through_the_writer(self):   # #934: the same rule, keyed by sid
        from species_photos import SpeciesPhotos
        d = tempfile.mkdtemp(); w = SpeciesPhotos(d)
        w.put('ann', srow('Ann Lee'), b'1'); w.put('elf', srow('Elf'), b'2'); w.put('mail', srow('Y'), b'3'); w.put('pd', srow('Y', 'Public domain'), b'4')
        w.pics['elf']['a'] = 'The original uploader was Elf at English Wikipedia.'; w.pics['mail']['a'] = 'x@y.com'; w.pics['pd']['a'] = 'x@y.com'; w.commit()
        w = SpeciesPhotos(d); self.assertEqual(w.dirty_authors(), ['elf', 'mail', 'pd'])
        cleaned, needs = c.clean_rows(w); self.assertEqual(needs, ['mail']); self.assertEqual([x[0] for x in cleaned], ['elf', 'pd'])
        w2 = SpeciesPhotos(d); self.assertEqual(w2.pics['elf']['a'], 'Elf'); self.assertEqual(w2.pics['pd']['a'], 'Unknown author'); self.assertEqual(w2.pics['mail']['a'], 'x@y.com'); self.assertEqual(w2.dirty_authors(), ['mail'])

if __name__ == '__main__': unittest.main()
