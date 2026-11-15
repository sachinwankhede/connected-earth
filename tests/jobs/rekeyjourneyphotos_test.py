"""jobs/rekeyjourneyphotos.py: each journey gets its own cover row by journey id without changing the picture it showed (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 3)."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs'))
import rekeyjourneyphotos as rk

def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj, bytes): open(p, 'wb').write(obj)
    else: json.dump(obj, open(p, 'w'))

def tree(author='X'):
    d = tempfile.mkdtemp()
    w(d, 'data/species/rows/ca/canis-lupus.json', {'sid': 'canis-lupus', 'latin': 'Canis lupus', 'name': 'Gray wolf', 'wiki': 'Gray wolf'})
    w(d, 'data/places/p.json', {'id': 'p', 'nodes': []})
    w(d, 'data/journeys/config.json', {'couple': 1, 'src': {}})
    for jid, img in (('wolf', 'Gray wolf'), ('wolf2', 'Gray wolf'), ('rain', 'Saharan Air Layer')):
        w(d, 'data/journeys/%s.json' % jid, {'pos': 0, 'id': jid, 'type': 'species', 'title': 'T', 'text': 't', 'imgwiki': img, 'ends': []})
    w(d, 'photos/species_hosted.json', {'Gray wolf': 'gw.webp'}); w(d, 'photos/species.json', {'Gray wolf': ['a/W.jpg/330px-W.jpg', 'Wolf']})
    w(d, 'photos/species_metadata.json', {'Gray wolf': {'a': author, 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:W.jpg'}})
    w(d, 'photos/species_large.json', {'Gray wolf': 'gw.webp'}); w(d, 'photos/species_source.json', {'Gray wolf': 'commons'})
    w(d, 'photos/species/gw.webp', b'small'); w(d, 'photos/species-lg/gw.webp', b'large')
    return d

def read(d, n): return json.load(open(os.path.join(d, 'photos', n + '.json')))

class RekeyTests(unittest.TestCase):
    def test_a_journey_gets_the_picture_and_credit_its_title_had(self):
        d = tree(); rk.migrate(d); pics = read(d, 'journey_pictures')
        self.assertEqual(sorted(pics), ['wolf', 'wolf2'])
        for jid in pics:
            self.assertEqual(pics[jid]['f'], jid + '.webp'); self.assertEqual((pics[jid]['a'], pics[jid]['l']), ('X', 'CC BY 4.0'))
            self.assertEqual((pics[jid]['wiki'], pics[jid]['page'], pics[jid]['src']), ('Gray wolf', 'Wolf', 'commons'))
            self.assertEqual(open(os.path.join(d, 'photos/journeys', jid + '.webp'), 'rb').read(), b'small')
        self.assertEqual(read(d, 'journey_large'), {'wolf': 'wolf.webp', 'wolf2': 'wolf2.webp'})
        self.assertEqual(open(os.path.join(d, 'photos/journeys-lg/wolf.webp'), 'rb').read(), b'large')

    def test_a_journey_with_no_hosted_title_is_recorded_as_missing_with_a_short_hold(self):
        d = tree(); rk.migrate(d)
        self.assertEqual(sorted(read(d, 'journey_missing')), ['rain']); self.assertEqual(read(d, 'journey_missing')['rain']['status'], 'notyet')
        self.assertFalse(os.path.exists(os.path.join(d, 'photos/journeys/rain.webp')))

    def test_the_species_files_stay_and_the_result_is_consistent(self):
        d = tree(); rk.migrate(d)
        self.assertTrue(os.path.exists(os.path.join(d, 'photos/species/gw.webp'))); self.assertTrue(os.path.exists(os.path.join(d, 'photos/species_hosted.json')))
        import journey_pics; self.assertEqual(journey_pics.check(d), [])

    def test_a_cc_by_picture_with_no_author_stops_the_migration(self):
        d = tree(author='')
        with self.assertRaises(SystemExit): rk.migrate(d)
        self.assertFalse(os.path.exists(os.path.join(d, 'photos', 'journey_pictures.json')))

    def test_dry_run_writes_nothing_and_a_second_run_refuses(self):
        d = tree(); rk.migrate(d, dry=True); self.assertFalse(os.path.exists(os.path.join(d, 'photos', 'journey_pictures.json')))
        self.assertFalse(os.path.exists(os.path.join(d, 'photos', 'journeys')))
        rk.migrate(d)
        with self.assertRaises(SystemExit): rk.migrate(d)

if __name__ == '__main__': unittest.main()
