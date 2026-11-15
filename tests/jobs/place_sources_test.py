#!/usr/bin/env python3
"""lib/place_sources.py: the contract every place picture source must meet (#887). Stubbed network only: no request leaves this test.
Every source registered in place_sources.SOURCES must, for a place it can find a picture for, yield a found Res whose row carries the same things (file page, licence, author, licence link, written by
the source) and whose picture bytes were downloaded from the thumbnail; and, run through placepictures.acquire, a CC BY / CC BY-SA picture with no author to be found must never be stored
(the author rule, `vet`), while one with an author is stored through PlacePhotos.put as <id>.jpg with the lists consistent.
Adding a source = a function and a line in SOURCES + one entry in WORLDS below: test_every_registered_source_has_a_stub fails until the stub exists."""
import io, os, sys, tempfile, unittest
from unittest import mock
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import place_sources as ps, placepictures as pj, place_photos as pp, author_lookup as al

def jpeg(size=(300, 250)):
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', size, (20, 90, 40)).save(b, 'JPEG'); return b.getvalue()

PICTURE = jpeg()
FILE = 'Alpha_Gorge_view.jpg'
THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/%s/330px-%s' % (FILE, FILE)
LU = 'https://creativecommons.org/licenses/by-sa/4.0/'
OV_ID = '0123456789abcdef0123456789abcdef0123'[:36]
UNIT = dict(id='aa', title='Alpha Gorge State Park', name='Alpha Gorge State Park', short='Alpha Gorge', lat=45.0, lon=-90.0, place='Maine, USA', region='Maine, USA')
UNKNOWN = ('Unknown author', 'Unknown', '')

def stub_wikipedia(author):
    def one(pid, title, out, man, where=''):
        with open(os.path.join(out, pid + '.jpg'), 'wb') as f: f.write(PICTURE)
        man[title] = dict(f=pid + '.jpg', a=author or 'Unknown author', l='CC BY-SA 4.0', lu=LU, p='https://commons.wikimedia.org/wiki/File:' + FILE, w='https://en.wikipedia.org/wiki/Alpha', checkedAt='x', fetchedAt='x')
        return 'ok'
    return [mock.patch.object(ps.ph, 'one', one)]

def commons_rows(author): return {FILE: ('CC BY-SA 4.0', author, LU, THUMB, 'image/jpeg')}

def stub_commons(author):
    return [mock.patch.object(ps.cs, 'resolve', lambda ts: {t: t for t in ts}), mock.patch.object(ps.cs, 'wikidata_images', lambda ts: {t: [FILE] for t in ts}),
            mock.patch.object(ps.cs, 'commons_info', lambda fs: commons_rows(author))]

def stub_nearby(author):
    return [mock.patch.object(ps, 'nearby', lambda lat, lon: [(FILE, 120)]), mock.patch.object(ps.cs, 'commons_info', lambda fs: commons_rows(author))]

def stub_category(author):
    return [mock.patch.object(ps, 'categories', lambda name: ['Alpha Gorge State Park']), mock.patch.object(ps, 'category_files', lambda c: [FILE]),
            mock.patch.object(ps.cs, 'commons_info', lambda fs: commons_rows(author))]

def stub_openverse(author):
    r = {'id': OV_ID, 'title': 'Alpha Gorge Maine', 'tags': [], 'license': 'by-sa', 'license_version': '4.0', 'creator': author, 'provider': 'flickr'}
    return [mock.patch.object(ps, 'openverse_search', lambda name, state='': [r])]

WORLDS = {'wikipedia': stub_wikipedia, 'commons': stub_commons, 'nearby': stub_nearby, 'category': stub_category, 'openverse': stub_openverse}

class World:
    """The stubbed network of one source: every download answers with PICTURE; Commons is asked for no author."""
    def __init__(self, name, author): self.patches = WORLDS[name](author) + [mock.patch.object(ps.wm, 'get', lambda u, raw=False, **k: PICTURE)]
    def __enter__(self):
        for p in self.patches: p.start()
        return self
    def __exit__(self, *a):
        for p in self.patches: p.stop()

def source(name): return [s for s in ps.SOURCES if s[0] == name][0]

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.w = pp.PlacePhotos(self.d); self.log = []; self._lookup = al.lookup; al.lookup = lambda fn: ('none', '')
    def tearDown(self): al.lookup = self._lookup
    def fresh(self): return pp.PlacePhotos(self.d)
    def acquire(self, name):
        if name != 'wikipedia' and not self.w.is_missing('aa'): self.w.miss('aa', 'nophoto', 'wikipedia')   # the later sources only try places Wikipedia gave nothing for
        return pj.acquire(self.w, [dict(UNIT)], [source(name)], log=self.log.append)

    def test_every_registered_source_has_a_stub(self):
        self.assertEqual([s[0] for s in ps.SOURCES], ['wikipedia', 'commons', 'nearby', 'category', 'openverse'], 'the order they are tried in')
        self.assertEqual(sorted(s[0] for s in ps.SOURCES), sorted(WORLDS), 'a source without a stub in WORLDS is not held to the contract')
        for name, find, applies, days in ps.SOURCES: self.assertTrue(callable(find) and callable(applies) and (days is None or days > 0), name)
        self.assertIs(pj.STRATEGIES, ps.SOURCES, 'placepictures runs exactly the registered sources')

    def test_a_found_candidate_has_the_same_shape_from_every_source(self):
        for name, find, applies, days in ps.SOURCES:
            with self.subTest(source=name), World(name, 'Jane Doe'):
                out = list(find([dict(UNIT)]))
                self.assertEqual(len(out), 1); u, r = out[0]; self.assertEqual((u['id'], r.kind), ('aa', 'found'), r.why)
                e = r.entry
                for k in ('f', 'a', 'l', 'lu', 'p', 'w', 'checkedAt', 'fetchedAt'): self.assertTrue(e.get(k), '%s: row has no %s' % (name, k))
                self.assertEqual((e['a'], e['f']), ('Jane Doe', 'aa.jpg'))
                self.assertTrue(e['p'].startswith('https://'), 'file page'); self.assertTrue(e['lu'].startswith('https://'), 'licence link'); self.assertTrue(e['l'].upper().startswith('CC'), 'licence')
                from PIL import Image
                self.assertEqual(Image.open(io.BytesIO(r.jpg)).format, 'JPEG', 'the thumbnail was downloaded')   # openverse re-encodes it to 330 px wide, the rest keep the bytes

    def test_the_author_rule_and_the_writer_apply_to_every_source(self):
        for name, find, applies, days in ps.SOURCES:
            for author in UNKNOWN:
                with self.subTest(source=name, author=author):
                    self.setUp()
                    with World(name, author): stats, stopped = self.acquire(name)
                    w = self.fresh()
                    self.assertFalse(w.has('aa'), 'a CC BY-SA picture with no author to be found is never stored'); self.assertEqual(stats[name]['found'], 0); self.assertEqual(stopped, [])
                    self.assertEqual(w.pics, {}); self.assertEqual(w.check(), [])
            with self.subTest(source=name, author='named'):
                self.setUp()
                with World(name, 'Jane Doe'): stats, _ = self.acquire(name)
                w = self.fresh(); self.assertTrue(w.has('aa')); self.assertEqual(stats[name]['found'], 1)
                r = w.pics['aa']; self.assertEqual((r['f'], r['a'], r['wiki']), ('aa.jpg', 'Jane Doe', UNIT['title'])); self.assertEqual(w.check(), [])
                self.assertTrue(os.path.exists(os.path.join(self.d, 'photos/places/aa.jpg')))

    def test_commons_sources_ask_commons_once_for_a_missing_author_and_use_the_name(self):
        for name in ('commons', 'nearby', 'category'):
            with self.subTest(source=name):
                self.setUp(); al.lookup = lambda fn: ('artist', 'Pat Smith')
                with World(name, 'Unknown author'): self.acquire(name)
                self.assertEqual(self.fresh().pics['aa']['a'], 'Pat Smith')

    def test_a_refused_picture_is_noted_so_the_source_does_not_ask_again_at_once(self):
        for name in ('commons', 'nearby', 'category'):
            with self.subTest(source=name):
                self.setUp()
                with World(name, 'Unknown author'): self.acquire(name)
                w = self.fresh(); self.assertIn(name, w.tried['aa'], 'noted in the ledger'); self.assertFalse(w.has('aa'))

    def test_the_writer_refuses_what_it_must_for_any_source(self):
        # PlacePhotos.put names the file <id>.jpg whatever the row says; a larger copy needs a picture; a place with a picture cannot be recorded missing
        with World('commons', 'Jane Doe'):
            (u, r), = list(source('commons')[1]([dict(UNIT)]))
        self.w.put('aa', dict(r.entry, f='other.jpg', wiki=UNIT['title']), r.jpg); self.assertEqual(self.w.pics['aa']['f'], 'aa.jpg')
        with self.assertRaises(ValueError): self.w.put_large('zz', b'x')
        with self.assertRaises(ValueError): self.w.miss('aa', 'nophoto', 'commons')
        with self.assertRaises(ValueError): self.w.note_tried('aa', 'commons')

if __name__ == '__main__': unittest.main()
