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
    def test_larger_pictures_are_checked(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}]}]})
            put(r, 'photos/species_hosted.json', {'A b': 'f.webp'}); put(r, 'photos/species/f.webp', b'x'); put(r, 'photos/species_metadata.json', {'A b': {'a': 'S', 'l': 'CC BY 4.0'}})
            put(r, 'photos/species_large.json', {'A b': 'f.webp'}); put(r, 'photos/species-lg/f.webp', b'x'); put(r, 'photos/species-lg/orphan.webp', b'x')
            errs, _ = check(r); text = ' | '.join(errs)
            self.assertIn('species-lg/orphan.webp is not listed', text); self.assertNotIn('is missing', text)
            os.remove(os.path.join(r, 'photos/species-lg/f.webp')); errs, _ = check(r)
            self.assertIn('file f.webp is missing', ' | '.join(errs))
    def test_problems_are_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', {'x': {'latin': 'Y y', 'name': 'n', 'tl': '2', 'wiki': 'w', 'desc': 'd'}})
            put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p', 'p', 'gone'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'zz'}]}]})
            put(r, 'data/outlines/stray.json', {})
            put(r, 'photos/species_hosted.json', {'A b': 'missing.webp'}); put(r, 'photos/species/orphan.webp', b'x'); put(r, 'photos/species.json', {'A b': [], 'Left out': []})
            errs, warns = check(r); text = ' | '.join(errs + warns)
            for want in ('neither hosted nor', "'ic' is a required property", 'own sid', "'sk' is a required property", 'not the lowercase Latin', "'2' is not of type 'integer'", 'duplicates', "'gone' has no file", "'zz' has no file", 'stray.json has no place', 'missing.webp is missing', 'author or licence missing', 'orphan.webp is not listed'):
                self.assertIn(want, text)

class JourneyEnds(unittest.TestCase):
    def test_a_journey_may_not_end_at_a_local_place(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {'level': 'local'}); put(r, 'data/places/q.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}, {'eco': 'q', 'node': 'n'}]}]})
            errs, _ = check(r); text = ' | '.join(errs)
            self.assertIn("journey 'j': place 'p' is local", text); self.assertNotIn("place 'q' is local", text)

class SchemasAndCrossFileRules(unittest.TestCase):
    """The schema files (build/schemas/) and the rules that look across files (#255)."""
    def tree(self, r):
        put(r, 'data/places/p.json', {}); put(r, 'data/order/0000-main.json', ['p'])
        put(r, 'data/species/rows/a-/a-b.json', SP['a b'])
    def test_clean_rows_layout(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r); self.assertEqual(check(r), ([], []))
    def test_species_row_problems(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            put(r, 'data/species/rows/zz/a-b.json', {**SP['a b'], 'sid': 'a-b', 'name': 'AB again'})   # wrong folder, same table key as ab/a-b.json
            put(r, 'data/species/rows/c-/c-d.json', {**SP['a b'], 'latin': 'C d', 'sid': 'c-d', 'sk': 'taxon', 'at': 'yesterday', 'extra': 1, 'cat': 'rock'})
            errs, _ = check(r); text = ' | '.join(errs)
            for want in ('belongs in a-/a-b.json', 'same table key', "'yesterday' does not match", "Additional properties are not allowed ('extra'", "'rock' is not one of"):
                self.assertIn(want, text)
    def test_outline_problems(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            put(r, 'data/outlines/p.json', {'n': 'P', 'r': [[0, 0, 1, 1, 2, 2, 3], [0, 0, 1, 1, 2, 95]], 's': 'google'})
            put(r, 'data/outlines/stray.json', {'n': 'S', 'r': [[0, 0, 1, 1, 2, 2]]})
            errs, _ = check(r); text = ' | '.join(errs)
            for want in ('ring 0 has an odd number', 'ring 1 has a point outside', "'google' is not one of", 'outline stray.json has no place'):
                self.assertIn(want, text)
    def test_job_written_lists(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            put(r, 'data/species/about.json', {'A': 'x', 'B': '', 'C': 3})
            put(r, 'data/text/summaries.json', {'p': 5})
            put(r, 'jobs/names.json', {'A b': None, 'C d': 'Cee', 'E f': 7})
            put(r, 'photos/species_missing.json', {'A b': 'nophoto', 'C d': 'gone'})
            put(r, 'photos/places/missing.json', {'Old': 'nophoto', 'New': {'status': 'nophoto', 'checkedAt': '2026-01-02T00:00:00', 'expiresAt': '2026-01-01T00:00:00', 'attempts': 0}})
            errs, warns = check(r); text = ' | '.join(errs); wtext = ' | '.join(warns)
            for want in ("3 is not of type 'string'", "5 is not of type 'string'", "7 is not of type", "'gone' is not one of", "0 is less than the minimum", 'expiresAt is not after checkedAt'):
                self.assertIn(want, text)
            self.assertIn('1 empty sentence', wtext); self.assertIn('1 old-format record', wtext)
    def test_geo_files(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            sq = {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
            put(r, 'data/geo/geo.json', {'countries': [{'id': '001', 'name': 'A', 'cont': 'X', 'g': sq}, {'id': '001', 'name': 'B', 'cont': 'X', 'g': sq},
                                                      {'id': 'undefined', 'name': 'C', 'cont': 'X', 'g': sq}, {'id': 'undefined', 'name': 'D', 'cont': 'X', 'g': sq}],
                                         'states': [{'id': '01', 'name': 'S', 'g': {'type': 'Point', 'coordinates': [0, 0]}}]})
            put(r, 'data/geo/land.json', {'type': 'Polygon', 'coordinates': []})
            errs, warns = check(r); text = ' | '.join(errs)
            for want in ("id '001' is repeated", "'Point' is not one of", "'MultiPolygon' was expected"):
                self.assertIn(want, text)
            self.assertIn("'undefined' is repeated", text); self.assertIn("should not be valid under", text)
    def test_journey_files_and_config(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            put(r, 'data/journeys/config.json', {'couple': 'half'})
            put(r, 'data/journeys/f.json', {'pos': 0, 'id': 'f', 'type': 'flow', 'title': 'F', 'text': 't', 'to': {'eco': 'p', 'node': 'n'}})
            errs, _ = check(r); text = ' | '.join(errs)
            for want in ("'from' is a required property", "'src' is a required property", "'half' is not of type 'number'"):
                self.assertIn(want, text)

if __name__ == '__main__': unittest.main()
