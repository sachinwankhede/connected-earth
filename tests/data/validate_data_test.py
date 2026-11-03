"""The data format check catches the mistakes it exists for, on a tiny throwaway tree."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build'))
from validate_data import check

def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj, bytes): open(p, 'wb').write(obj)
    else: json.dump(obj, open(p, 'w'))

SP = {'a b': {'latin': 'A b', 'name': 'AB', 'tl': 2, 'wiki': 'A b', 'desc': 'd', 'ic': 'x', 'sid': 'a-b', 'sk': 'taxon'}}

class DataFormat(unittest.TestCase):
    def test_clean_tree_has_no_problems(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}]}]})
            put(r, 'photos/species_hosted.json', {'A b': 'f.webp'}); put(r, 'photos/species/f.webp', b'x')
            put(r, 'photos/species_metadata.json', {'A b': {'a': 'Someone', 'l': 'CC BY 4.0'}})
            put(r, 'photos/species.json', {'A b': ['f.webp', 'A_b'], 'C d': ['x', 'C_d']}); put(r, 'photos/species_hosted_skipped.json', {'C d': 'not on Commons'})
            self.assertEqual(check(r), ([], []))
    def test_problems_are_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', {'x': {'latin': 'Y y', 'name': 'n', 'tl': '2', 'wiki': 'w', 'desc': 'd'}})
            put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p', 'p', 'gone'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'zz'}]}]})
            put(r, 'data/outlines/stray.json', {})
            put(r, 'photos/species_hosted.json', {'A b': 'missing.webp'}); put(r, 'photos/species/orphan.webp', b'x'); put(r, 'photos/species.json', {'A b': [], 'Left out': []})
            errs, warns = check(r); text = ' | '.join(errs + warns)
            for want in ('neither hosted nor', 'missing ic', 'own sid', 'sk must be', 'not the lowercase Latin', 'tl is not a whole', 'duplicates', "'gone' has no file", "'zz' has no file", 'stray.json has no place', 'missing.webp is missing', 'author or licence missing', 'orphan.webp is not listed'):
                self.assertIn(want, text)

if __name__ == '__main__': unittest.main()
