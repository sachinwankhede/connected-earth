"""jobs/nodepictures_migrate.py: the pictures filed as species rows for node labels get one record per concept, keyed by node id, without changing anything that exists (#976 step A)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs'))
import nodepictures_migrate as nm


def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj, bytes):
        with open(p, 'wb') as f: f.write(obj)
    else:
        with open(p, 'w') as f: json.dump(obj, f)


def read(p):
    with open(p) as f: return f.read()


CR = {'a': 'Jane Doe', 'l': 'CC BY-SA 4.0', 'lu': 'https://creativecommons.org/licenses/by-sa/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:Rain.jpg', 'page': 'Rain', 'wiki': 'Rain', 'u': 'a/b/Rain.jpg/330px-Rain.jpg'}


def tree():
    d = tempfile.mkdtemp()
    rows = {'heavy-rain': ('resource', 'Rain'), 'winter-rain': ('resource', 'Rain'), 'termitidae': ('taxon', 'Termite'), 'canis-lupus': ('taxon', 'Gray wolf')}
    for sid, (sk, wiki) in rows.items(): w(d, 'data/species/rows/%s/%s.json' % (sid[:2], sid), {'sid': sid, 'latin': sid, 'name': sid, 'wiki': wiki, 'sk': sk})
    pics = {'heavy-rain': dict(CR, f='r1.webp'), 'winter-rain': dict(CR, f='r1.webp'), 'termitidae': dict(CR, f='t1.webp', wiki='Termite', page='Termite'), 'canis-lupus': dict(CR, f='w1.webp', wiki='Gray wolf')}
    w(d, 'photos/species_pictures.json', pics); w(d, 'photos/species_medium.json', {'heavy-rain': 'r1.webp', 'winter-rain': 'r1.webp'})
    for f in ('r1', 't1', 'w1'): w(d, 'photos/species/%s.webp' % f, b'small-' + f.encode())
    w(d, 'photos/species-md/r1.webp', b'tile-rain')
    return d


class MigrateTests(unittest.TestCase):
    def test_many_label_rows_of_one_concept_become_one_node_record_and_taxa_stay(self):
        d = tree(); before = read(os.path.join(d, 'photos', 'species_pictures.json')); nm.migrate(d)
        pics = json.loads(read(os.path.join(d, 'photos', 'node_pictures.json')))
        self.assertEqual(sorted(pics), ['rain'], 'one record for the concept; the taxa (Termite, Gray wolf) are not resource rows')
        e = pics['rain']; self.assertEqual((e['a'], e['l'], e['wiki']), ('Jane Doe', 'CC BY-SA 4.0', 'Rain')); self.assertNotIn('u', e); self.assertNotIn('expires', e)
        self.assertTrue(e['built'] and e['checkedAt'])
        with open(os.path.join(d, 'photos', 'nodes', e['f']), 'rb') as f: self.assertEqual(f.read(), b'tile-rain', 'the 192 px tile is copied')
        self.assertEqual(read(os.path.join(d, 'photos', 'species_pictures.json')), before, 'nothing in the species data changes')
        self.assertTrue(os.path.exists(os.path.join(d, 'photos', 'species', 'r1.webp')))

    def test_dry_run_writes_nothing_and_a_second_run_is_refused(self):
        d = tree(); nm.migrate(d, dry=True); self.assertFalse(os.path.exists(os.path.join(d, 'photos', 'node_pictures.json')))
        nm.migrate(d)
        with self.assertRaises(SystemExit): nm.migrate(d)

    def test_an_unnamed_author_is_stored_as_the_writer_stores_it_and_the_round_trip_agrees(self):
        d = tree(); p = json.loads(read(os.path.join(d, 'photos', 'species_pictures.json')))
        for k in ('heavy-rain', 'winter-rain'): p[k]['a'] = 'Unknown'; p[k]['l'] = 'Public domain'
        w(d, 'photos/species_pictures.json', p); nm.migrate(d)
        self.assertEqual(json.loads(read(os.path.join(d, 'photos', 'node_pictures.json')))['rain']['a'], 'Unknown author')


if __name__ == '__main__': unittest.main()
