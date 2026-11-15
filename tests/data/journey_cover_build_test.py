"""build/build.py journey_cover_pictures and build/data_quality.py: the journey covers by journey id are additive and absent until photos/journey_pictures.json exists (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 2)."""
import json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import build as B
import journey_pics
import data_quality
journey_cover_row = data_quality.journey_cover_row

LINKS = {'cross': [{'id': 'osprey', 'imgwiki': 'Osprey'}, {'id': 'dust', 'imgwiki': 'Saharan Air Layer'}]}

def w(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f: json.dump(obj, f)

class CoverTests(unittest.TestCase):
    def test_no_new_files_adds_nothing(self):
        with tempfile.TemporaryDirectory() as r:
            self.assertEqual(B.journey_cover_pictures(journey_pics.load(r), LINKS), {}); self.assertEqual(journey_cover_row(r), '')

    def test_the_cover_comes_from_the_journeys_own_row(self):
        with tempfile.TemporaryDirectory() as r:
            w(r, 'photos/journey_pictures.json', {'osprey': {'f': 'osprey.webp', 'a': 'A', 'l': 'CC BY 4.0', 'lu': 'http://creativecommons.org/licenses/by/4.0', 'wiki': 'Osprey', 'page': 'Osprey_page', 'u': 'x'}})
            w(r, 'photos/journey_large.json', {'osprey': 'osprey.webp'}); w(r, 'photos/journey_missing.json', {'dust': {'status': 'notyet'}})
            out = B.journey_cover_pictures(journey_pics.load(r), LINKS)
            self.assertEqual(out['jpic'], {'osprey': ['osprey.webp', 'Osprey_page']}); self.assertEqual(out['jpicl'], ['osprey'])
            self.assertEqual(out['jpicm'], {'osprey': {'a': 'A', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0'}})   # https credit links, no bookkeeping fields
            w(r, 'data/journeys/config.json', {'couple': 1, 'src': {}})
            for j in ('osprey', 'dust'): w(r, 'data/journeys/%s.json' % j, {'pos': 0, 'id': j, 'type': 'flow'})
            self.assertIn('| Journey cover pictures | 1/2 |', journey_cover_row(r))

if __name__ == '__main__': unittest.main()
