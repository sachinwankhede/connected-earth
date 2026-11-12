import os, sys, json, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import droppictures as D

def put(root, name, data): json.dump(data, open(os.path.join(root, 'photos', name + '.json'), 'w'))
class DropTests(unittest.TestCase):
    def setUp(self):
        self.r = tempfile.mkdtemp()
        for s in ('species', 'species-lg'): os.makedirs(os.path.join(self.r, 'photos', s))
        for f, s in (('a.webp', 'species'), ('b.webp', 'species'), ('b.webp', 'species-lg')): open(os.path.join(self.r, 'photos', s, f), 'w').write('x')
        put(self.r, 'species_metadata', {'Good': {'l': 'CC BY 4.0', 'a': 'x', 'p': 'https://commons.wikimedia.org/wiki/File:A.jpg'}, 'Bad': {'l': 'GFDL 1.2', 'a': 'y', 'p': 'https://commons.wikimedia.org/wiki/File:B.jpg'}})
        put(self.r, 'species_hosted', {'Good': 'a.webp', 'Bad': 'b.webp'}); put(self.r, 'species_large', {'Bad': 'b.webp'})
        put(self.r, 'species', {'Good': ['p', 'G'], 'Bad': ['q', 'B']}); put(self.r, 'species_missing', {}); put(self.r, 'species_commons_tried', {'Bad': '2026-11-01'})
    def test_dry_changes_nothing(self):
        bad, c = D.drop(self.r, True); self.assertEqual(bad, ['Bad']); self.assertEqual(c['GFDL 1.2'], 1)
        self.assertTrue(os.path.exists(os.path.join(self.r, 'photos', 'species', 'b.webp')))
    def test_drop(self):
        D.drop(self.r)
        j = lambda n: json.load(open(os.path.join(self.r, 'photos', n + '.json')))
        self.assertEqual(j('species_hosted'), {'Good': 'a.webp'}); self.assertEqual(list(j('species_metadata')), ['Good']); self.assertEqual(j('species_large'), {})
        self.assertEqual(list(j('species')), ['Good']); self.assertEqual(j('species_missing'), {'Bad': 'nophoto'}); self.assertNotIn('Bad', j('species_commons_tried'))
        self.assertFalse(os.path.exists(os.path.join(self.r, 'photos', 'species', 'b.webp'))); self.assertFalse(os.path.exists(os.path.join(self.r, 'photos', 'species-lg', 'b.webp')))
        self.assertTrue(os.path.exists(os.path.join(self.r, 'photos', 'species', 'a.webp')))
    def test_layout_is_kept(self):
        put(self.r, 'species_hosted', {'Gu\u00e9': 'a.webp', 'Bad': 'b.webp'}); put(self.r, 'species_metadata', {'Gu\u00e9': {'l': 'CC0', 'p': 'x'}, 'Bad': {'l': 'FAL', 'p': 'y'}})
        D.drop(self.r); t = open(os.path.join(self.r, 'photos', 'species_hosted.json'), encoding='utf-8').read()
        self.assertEqual(t, '{\n"Gu\u00e9": "a.webp"\n}')   # one entry per line, accents as typed: the layout hostphotos.py writes
    def test_gbif_page_uses_gbif_rule(self):
        self.assertEqual(D.source_of({'p': 'https://www.gbif.org/occurrence/1'}), 'GBIF')
    def test_openverse_page_uses_openverse_rule(self):
        self.assertEqual(D.source_of({'p': 'https://openverse.org/image/abc'}), 'Openverse')
    def test_inaturalist_page_uses_inaturalist_rule(self):
        self.assertEqual(D.source_of({'p': 'https://www.inaturalist.org/photos/1'}), 'iNaturalist')
    def test_dropped_inaturalist_picture_is_marked_tried(self):
        put(self.r, 'species_metadata', {'Good': {'l': 'CC BY 4.0', 'p': 'https://commons.wikimedia.org/wiki/File:A.jpg'}, 'Bad': {'l': 'GFDL 1.2', 'p': 'https://www.inaturalist.org/photos/9'}})
        D.drop(self.r)
        self.assertEqual(list(json.load(open(os.path.join(self.r, 'photos', 'species_inaturalist_tried.json')))), ['Bad'])
    def test_title_drops_a_good_licence(self):
        bad, c = D.drop(self.r, False, ['Good', 'Nope']); self.assertEqual(bad, ['Good'])
        j = lambda n: json.load(open(os.path.join(self.r, 'photos', n + '.json')))
        self.assertEqual(j('species_hosted'), {'Bad': 'b.webp'}); self.assertEqual(j('species_missing'), {'Good': 'nophoto'})
        self.assertFalse(os.path.exists(os.path.join(self.r, 'photos', 'species', 'a.webp')))
    def test_dropped_openverse_picture_is_marked_tried(self):   # otherwise data-openversephotos fetches the same picture again (Acraea)
        put(self.r, 'species_metadata', {'Good': {'l': 'CC BY 4.0', 'p': 'https://commons.wikimedia.org/wiki/File:A.jpg'}, 'Acraea': {'l': 'CC BY-SA 2.0', 'p': 'https://openverse.org/image/abc'}, 'Bad': {'l': 'GFDL 1.2', 'p': 'https://commons.wikimedia.org/wiki/File:B.jpg'}})
        put(self.r, 'species_hosted', {'Good': 'a.webp', 'Acraea': 'a2.webp', 'Bad': 'b.webp'})
        D.drop(self.r, False, ['Acraea', 'Bad'])
        j = lambda n: json.load(open(os.path.join(self.r, 'photos', n + '.json')))
        self.assertEqual(list(j('species_openverse_tried')), ['Acraea'], 'only the Openverse picture is remembered as tried here')
        self.assertEqual(sorted(j('species_missing')), ['Acraea', 'Bad'])
class PlaceTests(unittest.TestCase):
    def test_places(self):
        r = tempfile.mkdtemp(); pd = os.path.join(r, 'photos', 'places'); os.makedirs(pd)
        for f in ('a.jpg', 'b.jpg', 'c.jpg'): open(os.path.join(pd, f), 'w').write('x')
        json.dump({'Good': {'f': 'a.jpg', 'l': 'CC BY-SA 2.0'}, 'Bad': {'f': 'b.jpg', 'l': 'GFDL 1.2'}, 'Vague': {'f': 'c.jpg', 'l': 'See file page'}}, open(os.path.join(pd, 'places.json'), 'w')); json.dump({}, open(os.path.join(pd, 'missing.json'), 'w'))
        bad, c = D.drop_places(r, True); self.assertEqual(bad, ['Bad', 'Vague']); self.assertTrue(os.path.exists(os.path.join(pd, 'b.jpg')))
        D.drop_places(r)
        self.assertEqual(list(json.load(open(os.path.join(pd, 'places.json')))), ['Good']); self.assertFalse(os.path.exists(os.path.join(pd, 'b.jpg'))); self.assertTrue(os.path.exists(os.path.join(pd, 'a.jpg')))
        m = json.load(open(os.path.join(pd, 'missing.json'))); self.assertEqual(sorted(m), ['Bad', 'Vague']); self.assertEqual(m['Bad']['status'], 'notfree')
    def test_place_job_uses_the_rule(self):   # jobs/photos.py talks to the network, so the test reads its source
        src = open(os.path.join(ROOT, 'jobs', 'photos.py')).read()
        self.assertIn("licences.ok('Wikimedia'", src); self.assertIn("return 'notfree'", src)
        import photo_registry; self.assertEqual(photo_registry.failure_class('notfree'), 'permanent')
if __name__ == '__main__': unittest.main()
