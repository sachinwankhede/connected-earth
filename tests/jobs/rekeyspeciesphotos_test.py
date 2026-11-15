"""jobs/rekeyspeciesphotos.py: the species pictures move from title keys to species ids without changing what any species shows (#934, phase 3)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs'))
import rekeyspeciesphotos as rk

def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj, bytes): open(p, 'wb').write(obj)
    else: json.dump(obj, open(p, 'w'))

def tree(author='X'):
    d = tempfile.mkdtemp()
    for sid, latin, wiki in (('canis-lupus', 'Canis lupus', 'Gray wolf'), ('rain', 'Rain', 'Rain'), ('rainfall', 'Rainfall', 'Rain'), ('acer-x', 'Acer x', 'Acer x'), ('bos-y', 'Bos y', 'Bos y')):
        w(d, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': latin, 'name': latin, 'wiki': wiki})
    w(d, 'data/places/p.json', {'id': 'p', 'nodes': [{'id': 'n', 'latin': 'Canis lupus', 'wiki': 'Arctic wolf'}]})
    w(d, 'photos/species.json', {'Gray wolf': ['a/W.jpg/330px-W.jpg', 'Wolf'], 'Arctic wolf': ['b/A.jpg/330px-A.jpg', 'Arctic_wolf'], 'Rain': ['c/R.jpg/330px-R.jpg', 'Rain']})
    w(d, 'photos/species_hosted.json', {'Gray wolf': 'gw.webp', 'Arctic wolf': 'aw.webp', 'Rain': 'rn.webp'})
    w(d, 'photos/species_metadata.json', {'Gray wolf': {'a': 'X', 'l': 'CC BY 4.0'}, 'Arctic wolf': {'a': 'Y', 'l': 'CC0'}, 'Rain': {'a': 'Z' if author else '', 'l': 'CC BY 4.0' if not author else 'CC0'}})
    w(d, 'photos/species_large.json', {'Gray wolf': 'gw.webp', 'Arctic wolf': 'aw.webp', 'Rain': 'rn.webp'}); w(d, 'photos/species_medium.json', {'Arctic wolf': 'aw.webp', 'Rain': 'rn.webp'})
    w(d, 'photos/species_missing.json', {'Acer x': 'nophoto'}); w(d, 'photos/species_hosted_skipped.json', {'Bos y': 'not on Commons'})
    w(d, 'photos/species_commons_tried.json', {'Acer x': '2026-11-06'}); w(d, 'photos/species_gbif_tried.json', {'Acer x': '2026-11-08'}); w(d, 'photos/species_source.json', {'Rain': 'openverse'})
    for f in ('gw', 'aw', 'rn'):
        for sub in ('species', 'species-md', 'species-lg'): w(d, 'photos/%s/%s.webp' % (sub, f), b'x')
    return d

def read(d, n): return json.load(open(os.path.join(d, 'photos', n + '.json')))

class RekeyTests(unittest.TestCase):
    def test_every_species_keeps_the_picture_it_showed(self):
        d = tree(); rk.migrate(d)
        pics = read(d, 'species_pictures')
        self.assertEqual(sorted(pics), ['canis-lupus', 'rain', 'rainfall'])
        self.assertEqual(pics['canis-lupus']['f'], 'aw.webp')   # the Latin name has no picture; the node title Arctic wolf is the first with one (not the row title Gray wolf)
        self.assertEqual(pics['rain']['f'], pics['rainfall']['f']); self.assertEqual(pics['rain']['src'], 'openverse')
        self.assertEqual(read(d, 'species_large'), {'canis-lupus': 'aw.webp', 'rain': 'rn.webp', 'rainfall': 'rn.webp'}); self.assertEqual(sorted(read(d, 'species_medium')), ['canis-lupus', 'rain', 'rainfall'])

    def test_misses_ledgers_and_skips_move_by_species(self):
        d = tree(); rk.migrate(d)
        self.assertEqual(sorted(read(d, 'species_missing')), ['acer-x', 'bos-y']); self.assertEqual(read(d, 'species_missing')['bos-y']['status'], 'notcommons')
        self.assertEqual(read(d, 'species_tried'), {'acer-x': {'commons': '2026-11-06', 'gbif': '2026-11-08'}})

    def test_old_lists_are_removed_and_the_unused_file_goes(self):
        d = tree(); rk.migrate(d)
        for n in rk.REPLACED: self.assertFalse(os.path.exists(os.path.join(d, 'photos', n + '.json')), n)
        self.assertFalse(os.path.exists(os.path.join(d, 'photos/species/gw.webp')))   # no species shows the Gray wolf title's picture any more
        import species_photos; self.assertEqual(species_photos.SpeciesPhotos(d).check(), [])

    def test_a_cc_by_picture_with_no_author_stops_the_migration(self):
        d = tree(author='')
        with self.assertRaises(SystemExit): rk.migrate(d)
        self.assertTrue(os.path.exists(os.path.join(d, 'photos', 'species_hosted.json')))   # nothing was written

    def test_dry_run_writes_nothing_and_a_second_run_refuses(self):
        d = tree(); rk.migrate(d, dry=True); self.assertFalse(os.path.exists(os.path.join(d, 'photos', 'species_pictures.json')))
        rk.migrate(d)
        with self.assertRaises(SystemExit): rk.migrate(d)

if __name__ == '__main__': unittest.main()
