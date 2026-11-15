"""lib/species_pics.py: the pictures by species id read the same from the old (title-keyed) and the new (sid-keyed) shape (#934, phase 2)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import species_pics as sp

def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

def old_shape():
    d = tempfile.mkdtemp()
    for sid, latin, wiki in (('canis-lupus', 'Canis lupus', 'Gray wolf'), ('rain', 'Rain', 'Rain'), ('rainfall', 'Rainfall', 'Rain'), ('acer-x', 'Acer x', 'Acer x')):
        w(d, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': latin, 'name': latin, 'wiki': wiki})
    w(d, 'photos/species.json', {'Gray wolf': ['a/ab/W.jpg/330px-W.jpg', 'Wolf'], 'Arctic wolf': ['b/bc/A.jpg/330px-A.jpg', 'Arctic_wolf'], 'Rain': ['c/cd/R.jpg/330px-R.jpg', 'Rain']})
    w(d, 'photos/species_hosted.json', {'Gray wolf': 'gw.webp', 'Arctic wolf': 'aw.webp', 'Rain': 'rn.webp'})
    w(d, 'photos/species_metadata.json', {'Gray wolf': {'a': 'X', 'l': 'CC BY 4.0'}, 'Arctic wolf': {'a': 'Y', 'l': 'CC0'}, 'Rain': {'a': 'Z', 'l': 'CC0'}})
    w(d, 'photos/species_large.json', {'Gray wolf': 'gw.webp', 'Rain': 'rn.webp'}); w(d, 'photos/species_medium.json', {'Gray wolf': 'gw.webp', 'Rain': 'rn.webp'})
    w(d, 'photos/species_missing.json', {'Acer x': 'nophoto'})
    return d

class ReaderTests(unittest.TestCase):
    def test_old_shape_gives_every_species_row_with_a_hosted_title_its_own_row(self):
        d = sp.load(old_shape()); self.assertEqual(d['shape'], 'title')
        self.assertEqual(sorted(d['pics']), ['canis-lupus', 'rain', 'rainfall'])   # a shared title gives each species the picture
        self.assertEqual(d['pics']['rain']['f'], d['pics']['rainfall']['f']); self.assertEqual(d['pics']['canis-lupus']['page'], 'Wolf')
        self.assertEqual(d['large']['rain'], 'rn.webp'); self.assertEqual(sorted(d['missing']), ['acer-x'])

    def test_node_titles_decide_which_picture_a_species_shows(self):
        d = sp.load(old_shape(), {'canis-lupus': {'Arctic wolf', 'Gray wolf'}})   # the old build took the Latin name first, then the sorted titles of its nodes
        self.assertEqual(d['pics']['canis-lupus']['f'], 'aw.webp'); self.assertEqual(d['pics']['canis-lupus']['wiki'], 'Arctic wolf')

    def test_every_hosted_title_is_in_the_title_view_for_the_journeys(self):
        d = sp.load(old_shape()); self.assertEqual(sorted(d['titles']), ['Arctic wolf', 'Gray wolf', 'Rain']); self.assertEqual(sorted(d['title_large']), ['Gray wolf', 'Rain'])

    def test_new_shape_is_read_as_it_is(self):
        r = tempfile.mkdtemp(); w(r, 'photos/species_pictures.json', {'canis-lupus': {'f': 'gw.webp', 'a': 'X', 'l': 'CC BY 4.0', 'wiki': 'Gray wolf', 'page': 'Wolf'}})
        w(r, 'photos/species_large.json', {'canis-lupus': 'gw.webp'})
        d = sp.load(r); self.assertEqual(d['shape'], 'sid'); self.assertEqual(d['pics']['canis-lupus']['page'], 'Wolf'); self.assertEqual(d['titles']['Gray wolf']['f'], 'gw.webp')
        self.assertEqual(d['title_large'], {'Gray wolf': 'gw.webp'}); self.assertEqual(d['medium'], {}); self.assertEqual(d['missing'], {})

    def test_credit_is_the_credit_fields_only(self):
        self.assertEqual(sp.credit({'f': 'x.webp', 'wiki': 'T', 'page': 'P', 'u': 'a/b', 'a': 'X', 'l': 'CC0', 'lu': '', 'p': 'https://c'}), {'a': 'X', 'l': 'CC0', 'lu': '', 'p': 'https://c'})

    def test_legacy_lists_equal_the_old_files(self):
        r = old_shape(); L = sp.legacy_lists(r)
        for n in ('species', 'species_hosted', 'species_metadata', 'species_large'): self.assertEqual(L[n], json.load(open(os.path.join(r, 'photos', n + '.json'))) if n != 'species_large' and n != 'species' else L[n])
        self.assertEqual(L['species_hosted'], {'Gray wolf': 'gw.webp', 'Arctic wolf': 'aw.webp', 'Rain': 'rn.webp'}); self.assertEqual(L['species_large'], {'Gray wolf': 'gw.webp', 'Rain': 'rn.webp'})
        self.assertEqual(L['species']['Gray wolf'], ['a/ab/W.jpg/330px-W.jpg', 'Wolf'])

if __name__ == '__main__': unittest.main()
