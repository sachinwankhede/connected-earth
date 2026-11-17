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
    def test_a_species_sid_must_be_the_slug_of_its_name_but_a_resource_may_differ(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', {'a b': dict(SP['a b'], sid='a-b-2'), 'soil': {'name': 'Soil', 'tl': 0, 'ic': 'x', 'sid': 'soil-2', 'sk': 'resource', 'cat': 'rock'}}); put(r, 'data/places/p.json', {})
            errs, _ = check(r); text = '\n'.join(errs)
            self.assertIn("species 'a b': its sid 'a-b-2' is not the slug of its name ('a-b')", text)
            self.assertEqual(sum('slug of its name' in e for e in errs), 1)   # the resource row is not reported
    def test_clean_tree_has_no_problems(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}]}]})
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Someone', 'l': 'CC BY 4.0', 'wiki': 'A b'}}); put(r, 'photos/species/f.webp', b'x')
            self.assertEqual(check(r), ([], []))
    def test_larger_and_tile_species_copies_are_checked(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'S', 'l': 'CC BY 4.0', 'wiki': 'A b'}}); put(r, 'photos/species/f.webp', b'x')
            put(r, 'photos/species_large.json', {'a-b': 'f.webp'}); put(r, 'photos/species-lg/f.webp', b'x'); put(r, 'photos/species-lg/orphan.webp', b'x')
            put(r, 'photos/species_medium.json', {'a-b': 'f.webp'}); put(r, 'photos/species-md/f.webp', b'x'); put(r, 'photos/species-md/orphan2.webp', b'x')
            text = ' | '.join(check(r)[0])
            self.assertIn('species-lg/orphan.webp is not listed', text); self.assertIn('species-md/orphan2.webp is not listed', text); self.assertNotIn('is missing', text)
            os.remove(os.path.join(r, 'photos/species-lg/f.webp')); self.assertIn('f.webp is missing', ' | '.join(check(r)[0]))
    def test_a_species_copy_of_another_file_than_its_picture_is_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'S', 'l': 'CC0', 'wiki': 'A b'}}); put(r, 'photos/species/f.webp', b'x')
            put(r, 'photos/species_medium.json', {'a-b': 'g.webp'}); put(r, 'photos/species-md/g.webp', b'x')
            self.assertTrue([e for e in check(r)[0] if 'medium copy' in e and 'not the file of its picture' in e])
    def test_species_with_both_a_picture_and_a_miss_and_unknown_sids_are_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            miss = {'status': 'nophoto', 'checkedAt': '2026-11-15T12:00:00+00:00', 'expiresAt': '2027-05-14T12:00:00+00:00', 'attempts': 1}
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'S', 'l': 'CC0', 'wiki': 'A b'}, 'zz': {'f': 'f.webp', 'a': 'S', 'l': 'CC0'}}); put(r, 'photos/species/f.webp', b'x')
            put(r, 'photos/species_missing.json', {'a-b': miss, 'yy': miss}); put(r, 'photos/species_tried.json', {'xx': {'commons': '2026-11-15'}})
            text = ' | '.join(check(r)[0])
            self.assertIn('a-b: has a picture and is also in species_missing.json', text)
            for sid, f in (('zz', 'species_pictures.json'), ('yy', 'species_missing.json'), ('xx', 'species_tried.json')): self.assertIn("photos/%s: '%s' is not a species row" % (f, sid), text)
    def test_a_species_cc_by_picture_with_no_author_fails_and_so_does_a_dirty_author(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {}); put(r, 'photos/species/f.webp', b'x')
            for lic in ('CC BY 4.0', 'CC BY-SA 3.0'):
                put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Unknown author', 'l': lic, 'wiki': 'A b'}}); self.assertTrue([e for e in check(r)[0] if 'no named author' in e])
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Unknown author', 'l': 'CC0', 'wiki': 'A b'}}); self.assertEqual(check(r), ([], []))
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Beeblebrox (talk) 06:06, 13 January 2009 (UTC)', 'l': 'CC BY 4.0', 'wiki': 'A b'}})
            errs, warns = check(r); self.assertTrue([e for e in errs if 'species_pictures.json' in e and 'need cleaning' in e]); self.assertEqual([w for w in warns if 'need cleaning' in w], [])   # an error since the 15 Nov cleanauthors data (#964)
    def test_a_stray_non_webp_file_in_a_species_folder_is_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {}); put(r, 'photos/species/x.jpg', b'x')
            self.assertTrue([e for e in check(r)[0] if 'x.jpg is not a .webp' in e])
    def test_larger_place_pictures_are_checked_the_same_way_when_the_list_is_keyed_by_place_id(self):   # the new shape (#887): key = place id, the title in `wiki`
        with tempfile.TemporaryDirectory() as r:
            put(r, 'photos/places/places.json', {'okpark': {'f': 'okpark.jpg', 'wiki': 'Park', 'a': 'Someone', 'l': 'CC BY 4.0'}}); put(r, 'photos/places_large.json', {'okpark': 'okpark.webp'}); put(r, 'photos/places-lg/okpark.webp', b'x')
            self.assertEqual([e for e in check(r)[0] if 'larger place' in e or 'places-lg' in e], [])
            put(r, 'photos/places-lg/stray.webp', b'x'); self.assertTrue([e for e in check(r)[0] if 'stray.webp is not listed' in e])
            os.remove(os.path.join(r, 'photos/places-lg/stray.webp')); put(r, 'photos/places/okpark.jpg', b'x'); put(r, 'photos/places/places.json', {})   # the picture is gone, its larger copy is not: the Arrowhead case
            self.assertTrue([e for e in check(r)[0] if 'larger copy but no stored picture' in e])
    def test_a_stored_place_picture_with_no_author_is_found(self):   # CC BY needs a named author (#887)
        with tempfile.TemporaryDirectory() as r:
            put(r, 'photos/places/places.json', {'okpark': {'f': 'okpark.jpg', 'a': 'Unknown author', 'l': 'CC BY-SA 4.0'}}); put(r, 'photos/places/okpark.jpg', b'x')
            self.assertTrue([e for e in check(r)[0] if 'no named author' in e])
            put(r, 'photos/places/places.json', {'okpark': {'f': 'okpark.jpg', 'a': 'Unknown author', 'l': 'CC0'}})
            self.assertEqual([e for e in check(r)[0] if 'okpark' in e], [])
    def test_a_stored_place_author_that_needs_cleaning_is_an_error(self):   # an email, a talk stamp, a web address or an uploader sentence is not the stored form (lib/author_clean.py)
        import validate_data
        self.assertTrue(validate_data.DIRTY_AUTHOR_IS_ERROR)
        with tempfile.TemporaryDirectory() as r:
            put(r, 'photos/places/places.json', {'okpark': {'f': 'okpark.jpg', 'a': 'Beeblebrox (talk) 06:06, 13 January 2009 (UTC)', 'l': 'CC BY 4.0'}}); put(r, 'photos/places/okpark.jpg', b'x')
            errs, warns = check(r); self.assertTrue([e for e in errs if 'need cleaning' in e and 'okpark' in e]); self.assertEqual([w for w in warns if 'need cleaning' in w], [])
            put(r, 'photos/places/places.json', {'okpark': {'f': 'okpark.jpg', 'a': 'Beeblebrox', 'l': 'CC BY 4.0'}})
            self.assertEqual([e for e in check(r)[0] if 'need cleaning' in e], [])
    def test_species_pictures_by_species_id_are_checked_by_their_writer(self):   # the new shape (#934): files, rows, copies, authors agree
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', dict(SP, **{'c d': dict(SP['a b'], latin='C d', sid='c-d', wiki='C d')})); put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}]}]})
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Someone', 'l': 'CC BY 4.0', 'wiki': 'A b'}}); put(r, 'photos/species/f.webp', b'x')
            self.assertEqual(check(r), ([], []))
            put(r, 'photos/species_large.json', {'a-b': 'f.webp'}); self.assertTrue([e for e in check(r)[0] if 'species_large.json' in e and 'missing' in e])
            put(r, 'photos/species-lg/f.webp', b'x'); put(r, 'photos/species/stray.webp', b'x')
            self.assertEqual([e for e in check(r)[0] if 'large' in e], []); self.assertTrue([e for e in check(r)[0] if 'stray.webp' in e])
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': '', 'l': 'CC BY 4.0', 'wiki': 'A b'}})
            self.assertTrue([e for e in check(r)[0] if 'no named author' in e])
            put(r, 'photos/species_pictures.json', {'a-b': {'f': 'f.webp', 'a': 'Someone', 'l': 'CC BY 4.0', 'wiki': 'A b'}})
            put(r, 'photos/species_missing.json', {'c-d': {'status': 'nophoto', 'checkedAt': '2026-11-15T12:00:00+00:00', 'expiresAt': '2027-05-14T12:00:00+00:00', 'attempts': 1}})   # a miss by species id is a record, not a word
            self.assertEqual([e for e in check(r)[0] if 'species_missing' in e], [])
            put(r, 'photos/species_missing.json', {'c-d': 'nophoto'}); self.assertTrue([e for e in check(r)[0] if 'species_missing' in e])
    def test_journey_pictures_by_journey_id_are_checked_by_their_writer_and_absent_files_change_nothing(self):   # phase 2 of the journey pictures (#945)
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP); put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'p', 'node': 'n'}]}]})
            self.assertEqual([e for e in check(r)[0] if 'journey' in e.lower() and 'picture' in e.lower()], [])   # no photos/journey_pictures.json: nothing to check
            put(r, 'photos/journey_pictures.json', {'j': {'f': 'j.webp', 'a': 'Someone', 'l': 'CC BY 4.0', 'wiki': 'T'}}); put(r, 'photos/journeys/j.webp', b'x')
            self.assertEqual([e for e in check(r)[0] if 'journey' in e], [])
            put(r, 'photos/journeys/stray.webp', b'x'); put(r, 'photos/journey_pictures.json', {'j': {'f': 'j.webp', 'a': 'Someone', 'l': 'CC BY 4.0'}, 'zz': {'f': 'zz.webp', 'a': 'S', 'l': 'CC0'}})
            text = ' | '.join(check(r)[0])
            self.assertIn('stray.webp is not listed', text); self.assertIn('zz is not a journey id', text); self.assertIn('zz.webp is missing', text)
            put(r, 'photos/journey_pictures.json', {'j': {'f': 'j.webp', 'a': '', 'l': 'CC BY 4.0'}}); self.assertIn('no named author', ' | '.join(check(r)[0]))
    def test_a_food_web_node_naming_a_species_row_that_is_not_there_is_found(self):   # #973 phase 4
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', SP)
            put(r, 'data/places/p.json', {'nodes': [{'id': 'n1', 'sp': 'a b', 'xh': 0.5}]})
            self.assertEqual([e for e in check(r)[0] if 'names species row' in e], [])
            put(r, 'data/places/p.json', {'nodes': [{'id': 'n1', 'sp': 'a b', 'xh': 0.5}, {'id': 'n2', 'sp': 'gone', 'xh': 0.5}]})
            self.assertEqual(len([e for e in check(r)[0] if "node 'n2' names species row 'gone'" in e]), 1)
    def test_problems_are_found(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/species/species.json', {'x': {'latin': 'Y y', 'name': 'n', 'tl': '2', 'wiki': 'w', 'desc': 'd'}})
            put(r, 'data/places/p.json', {})
            put(r, 'data/journeys/links.json', {'order': ['p', 'p', 'gone'], 'cross': [{'id': 'j', 'type': 'species', 'title': 'T', 'text': 'x', 'ends': [{'eco': 'zz'}]}]})
            put(r, 'data/outlines/stray.json', {})
            put(r, 'photos/species_pictures.json', {'zz': {'f': 'missing.webp', 'a': '', 'l': 'CC BY 4.0'}}); put(r, 'photos/species/orphan.webp', b'x')
            errs, warns = check(r); text = ' | '.join(errs + warns)
            for want in ("'ic' is a required property", 'own sid', "'sk' is a required property", 'not the lowercase Latin', "'2' is not of type 'integer'", 'duplicates', "'gone' has no file", "'zz' has no file", 'stray.json has no place', 'missing.webp is missing', 'no named author', 'orphan.webp is not listed', "'zz' is not a species row"):
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
            put(r, 'photos/species_missing.json', {'a-b': {'status': 'gone', 'checkedAt': '2026-01-01T00:00:00', 'expiresAt': '2026-02-01T00:00:00', 'attempts': 1}})
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
    def shared_tree(self, r):
        put(r, 'data/places/a.json', {'imgwiki': 'Same'}); put(r, 'data/places/b.json', {'imgwiki': 'Same'})
        put(r, 'data/places/c.json', {'imgwiki': 'Own'}); put(r, 'data/places/d.json', {})
    def test_shared_imgwiki_is_an_error(self):
        import validate_data
        self.assertTrue(validate_data.SHARED_IMGWIKI_IS_ERROR)
        with tempfile.TemporaryDirectory() as r:
            self.shared_tree(r); errs, warns = check(r)
            e = [x for x in errs if 'imgwiki' in x]
            self.assertEqual(len(e), 1); self.assertIn('1 imgwiki title(s) shared by 2 places', e[0]); self.assertIn('Same (a, b)', e[0]); self.assertNotIn('Own', e[0])
            self.assertEqual([x for x in warns if 'imgwiki' in x], [])
    def test_unique_imgwiki_is_silent(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/places/a.json', {'imgwiki': 'A'}); put(r, 'data/places/b.json', {'imgwiki': 'B'})
            self.assertEqual([x for x in check(r)[1] if 'imgwiki' in x], [])

if __name__ == '__main__': unittest.main()
