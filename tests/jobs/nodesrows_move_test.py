#!/usr/bin/env python3
"""#976: the one-time move of node rows out of the species rows (jobs/nodesrows_move.py)."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
for d in ('jobs', 'lib', 'build'): sys.path.insert(0, os.path.join(ROOT, d))
import nodesrows_move as m, species_photos, species


def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f: json.dump(obj, f)


class MoveTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        for sid, sk in (('wolf', 'taxon'), ('soil', 'resource'), ('rain', 'resource')):
            w(self.root, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': '' if sk == 'resource' else 'Canis', 'name': sid, 'sk': sk, 'tl': 0, 'wiki': sid, 'desc': 'd', 'ic': 'x'})
        s = species_photos.SpeciesPhotos(self.root)
        for sid in ('wolf', 'soil'): s.put(sid, {'a': 'Ann', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0/', 'p': 'https://x/' + sid}, sid.encode())
        s.miss('rain', 'notfound'); s.commit()

    def test_node_rows_move_and_species_stay(self):
        r = m.move(self.root); self.assertEqual(r['rows'], 2)
        self.assertTrue(os.path.exists(os.path.join(self.root, 'data/nodes/rows/so/soil.json')))
        self.assertTrue(os.path.exists(os.path.join(self.root, 'data/species/rows/wo/wolf.json')))
        self.assertFalse(os.path.exists(os.path.join(self.root, 'data/species/rows/so')))
        self.assertEqual(set(species.table(self.root)), {'canis', 'soil', 'rain'})   # both folders are read

    def test_their_pictures_leave_the_species_lists(self):
        m.move(self.root); s = species_photos.SpeciesPhotos(self.root)
        self.assertEqual(set(s.pics), {'wolf'}); self.assertEqual(s.miss_, {})
        self.assertEqual(s.check(), [])

    def test_dry_run_changes_nothing_and_a_second_run_refuses(self):
        m.move(self.root, dry=True); self.assertFalse(os.path.exists(os.path.join(self.root, 'data/nodes')))
        m.move(self.root)
        with self.assertRaises(SystemExit): m.move(self.root)

    def test_a_new_node_row_is_written_to_the_node_folder(self):
        m.move(self.root); old = species.ROWS, species.NODES
        try:
            species.ROWS = os.path.join(self.root, 'data/species/rows'); species.NODES = os.path.join(self.root, 'data/nodes/rows')
            species.write_row({'sid': 'sun', 'sk': 'resource', 'name': 'Sun'}); species.write_row({'sid': 'ox', 'sk': 'taxon', 'name': 'Ox'})
        finally: species.ROWS, species.NODES = old
        self.assertTrue(os.path.exists(os.path.join(self.root, 'data/nodes/rows/su/sun.json'))); self.assertTrue(os.path.exists(os.path.join(self.root, 'data/species/rows/ox/ox.json')))


if __name__ == '__main__': unittest.main()
