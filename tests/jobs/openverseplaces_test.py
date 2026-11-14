#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
import openverseplaces as v
import photo_registry as pr

ID = '0123456789abcdef0123456789abcdef0123'[:36]
def res(title, tags=(), lic='by', ver='4.0', creator='Ann', **kw):
    return dict({'id': ID, 'title': title, 'tags': [{'name': t} for t in tags], 'license': lic, 'license_version': ver, 'creator': creator, 'provider': 'flickr'}, **kw)

class PlaceTests(unittest.TestCase):
    def test_only_us_places_have_a_state(self):
        self.assertEqual(v.where_of('Maine, USA'), 'Maine'); self.assertEqual(v.where_of('Kenya'), ''); self.assertEqual(v.where_of(None), '')

    def test_the_title_or_tags_must_name_the_place_and_the_state(self):
        self.assertEqual(len(v.candidates([res('Trout Pond in Maine')], 'Trout Pond', 'Maine')), 1)
        self.assertEqual(len(v.candidates([res('Pond view', ['trout pond', 'maine'])], 'Trout Pond', 'Maine')), 1)
        self.assertEqual(v.candidates([res('Trout Pond, West Virginia')], 'Trout Pond', 'Maine'), [], 'another state is not this place')
        self.assertEqual(v.candidates([res('A pond in Maine')], 'Trout Pond', 'Maine'), [], 'the place name must be there')

    def test_licence_creator_and_non_photos_are_checked(self):
        self.assertEqual(v.candidates([res('Trout Pond Maine', lic='by-nc')], 'Trout Pond', 'Maine'), [])
        self.assertEqual(v.candidates([res('Trout Pond Maine', creator='')], 'Trout Pond', 'Maine'), [])
        self.assertEqual(v.candidates([res('Trout Pond Maine map')], 'Trout Pond', 'Maine'), [])
        self.assertEqual(v.candidates([res('Trout Pond Maine', provider='inaturalist')], 'Trout Pond', 'Maine'), [])
        c = v.candidates([res('Trout Pond Maine', lic='cc0', ver='1.0')], 'Trout Pond', 'Maine')[0]
        self.assertEqual((c[2], c[3]), ('Ann', 'CC0 1.0')); self.assertTrue(c[1].startswith('https://api.openverse.org/v1/images/') and c[1].endswith('/thumb/'))

    def test_a_dry_run_says_why_a_place_found_nothing(self):
        rr, ex = v.reject_reasons([res('Trout Pond, West Virginia'), res('Trout Pond Maine', lic='by-nc'), res('Trout Pond Maine', creator=''), res('Trout Pond Maine map')], 'Trout Pond', 'Maine')
        self.assertEqual(rr, {'place or state not in title or tags': 1, 'licence': 1, 'no creator': 1, 'not a photo or unwanted source': 1}); self.assertEqual(ex, ['Trout Pond, West Virginia'])

    def test_the_query_is_the_exact_name_only(self):
        seen = []
        with mock.patch.object(v.wm, 'get', lambda u, **k: seen.append(u) or {'results': []}):
            v.search('Trout Pond', 'Maine')
        import urllib.parse
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(seen[0]).query)
        self.assertEqual(q['q'], ['"Trout Pond"']); self.assertNotIn('Maine', seen[0])

    def test_the_entry_validates_as_a_place_credit(self):
        e = v.entry('metroutpond', 'Ann', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0', ID, 'now')
        self.assertTrue(pr.safe_https(e['p'], pr.PLACE_CREDIT_HOSTS)); self.assertEqual(e['f'], 'metroutpond.jpg')
        self.assertFalse(pr.safe_https('https://evil.example/openverse.org', pr.PLACE_CREDIT_HOSTS))

    def test_the_jpeg_is_330_wide_and_small_pictures_are_refused(self):
        import io
        from PIL import Image
        def png(w, h): b = io.BytesIO(); Image.new('RGB', (w, h), (10, 120, 30)).save(b, 'PNG'); return b.getvalue()
        out = Image.open(io.BytesIO(v.to_jpeg(png(800, 600)))); self.assertEqual((out.format, out.size), ('JPEG', (330, 248)))
        self.assertIsNone(v.to_jpeg(png(150, 400))); self.assertIsNone(v.to_jpeg(b'not an image'))

if __name__ == '__main__':
    unittest.main()
