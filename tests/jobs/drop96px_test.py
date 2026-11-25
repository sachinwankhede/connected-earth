#!/usr/bin/env python3
"""#1188: the 192 px picture is the stored picture of species and journeys, no 96 px file is written, and jobs/drop96px.py migrates old data (dry run lists the right files). Offline: fake fetch, temp roots."""
import io, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
from PIL import Image
import drop96px, speciespictures as sj, species_photos as sp, journey_photos as jp, journeypictures as jj, species_sources as ss


def webp(w, h, color=(10, 80, 30)):
    b = io.BytesIO(); Image.new('RGB', (w, h), color).save(b, 'WEBP'); return b.getvalue()

def jpeg(size=(1000, 500)):
    b = io.BytesIO(); Image.new('RGB', size, (20, 90, 40)).save(b, 'JPEG'); return b.getvalue()

def size_of(path):
    with Image.open(path) as im: return im.size

def row(f=None, **kw):
    r = dict(a='Jane Doe', l='CC BY 4.0', lu='https://creativecommons.org/licenses/by/4.0/', p='https://commons.wikimedia.org/wiki/File:S.jpg', page='S', u='a/ab/S.jpg/330px-S.jpg', wiki='S')
    if f: r['f'] = f
    return dict(r, **kw)

def write(d, rel, data):
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f: f.write(data if isinstance(data, bytes) else json.dumps(data).encode())

def old_species_root():
    """Old shape: aa has 96 px + 192 px + 400 px; bb has 96 px + 400 px only; cc has 96 px only; dd and ee share one picture (dd has a 192 px copy, ee has not)."""
    d = tempfile.mkdtemp()
    pics = {'aa': row('aaaaaaaaaaaa.webp'), 'bb': row('bbbbbbbbbbbb.webp'), 'cc': row('cccccccccccc.webp'), 'dd': row('dddddddddddd.webp'), 'ee': row('dddddddddddd.webp')}
    write(d, 'photos/species_pictures.json', pics)
    for f in ('aaaaaaaaaaaa', 'bbbbbbbbbbbb', 'cccccccccccc', 'dddddddddddd'): write(d, 'photos/species/%s.webp' % f, webp(96, 64))
    write(d, 'photos/species-md/aaaaaaaaaaaa.webp', webp(192, 128)); write(d, 'photos/species-md/dddddddddddd.webp', webp(192, 128))
    write(d, 'photos/species_medium.json', {'aa': 'aaaaaaaaaaaa.webp', 'dd': 'dddddddddddd.webp'})
    for f in ('aaaaaaaaaaaa', 'bbbbbbbbbbbb', 'dddddddddddd'): write(d, 'photos/species-lg/%s.webp' % f, webp(400, 267))
    write(d, 'photos/species_large.json', {'aa': 'aaaaaaaaaaaa.webp', 'bb': 'bbbbbbbbbbbb.webp', 'dd': 'dddddddddddd.webp', 'ee': 'dddddddddddd.webp'})
    return d

def old_journey_root():
    d = tempfile.mkdtemp()
    write(d, 'photos/journey_pictures.json', {'osprey': row('osprey.webp'), 'knot': row('knot.webp'), 'big': row('big.webp')})
    write(d, 'photos/journeys/osprey.webp', webp(96, 64)); write(d, 'photos/journeys/knot.webp', webp(96, 64)); write(d, 'photos/journeys/big.webp', webp(192, 128))
    write(d, 'photos/journeys-lg/osprey.webp', webp(400, 267)); write(d, 'photos/journeys-lg/big.webp', webp(400, 267)); write(d, 'photos/journey_large.json', {'osprey': 'osprey.webp', 'big': 'big.webp'})
    return d


class NewPicturesAre192(unittest.TestCase):
    def test_a_species_picture_is_192_px_with_no_96_px_file_and_the_400_px_copy_from_the_larger_download(self):
        d = tempfile.mkdtemp(); write(d, 'photos/species_pictures.json', {}); w = sp.SpeciesPhotos(d); log = []
        def find(todo):
            for u in todo: yield u, ss.Res('found', row(), jpeg((330, 220)), note='S.jpg')
        got = []
        def get(u, raw=False): got.append(u); return jpeg((1000, 500))
        sj.acquire(w, [dict(sid='aa', title='Aa', name='Aa', latin='Aa', abiotic=False)], [('wikipedia', find, lambda w, u: True, None)], log=log.append, copies=lambda e, need=('medium', 'large'): sj.make_copies(e, need, get))
        w = sp.SpeciesPhotos(d); f = w.pics['aa']['f']
        self.assertEqual(max(size_of(os.path.join(d, 'photos/species-md', f))), 192); self.assertEqual(max(size_of(os.path.join(d, 'photos/species-lg', f))), 400)
        self.assertFalse(os.path.exists(os.path.join(d, 'photos/species'))); self.assertEqual(w.check(), []); self.assertEqual(len(got), 1, 'one download for the 400 px copy only')

    def test_the_400_px_copy_falls_back_to_the_192_px_picture_and_the_failed_copy_is_held_30_days(self):
        d = tempfile.mkdtemp(); write(d, 'photos/species_pictures.json', {}); w = sp.SpeciesPhotos(d)
        def find(todo):
            for u in todo: yield u, ss.Res('found', row(), jpeg((330, 220)), note='S.jpg')
        def get(u, raw=False): raise RuntimeError('HTTP 400')
        sj.acquire(w, [dict(sid='aa', title='Aa', name='Aa', latin='Aa', abiotic=False)], [('wikipedia', find, lambda w, u: True, None)], log=lambda m: None, copies=lambda e, need=('medium', 'large'): sj.make_copies(e, need, get))
        w = sp.SpeciesPhotos(d); self.assertTrue(w.has_medium('aa')); self.assertFalse(w.has_large('aa')); self.assertEqual(w.check(), [])
        import datetime; self.assertTrue(w.copy_held('aa', datetime.date.today())); self.assertFalse(w.copy_held('aa', datetime.date.today() + datetime.timedelta(days=31)))

    def test_a_journey_cover_is_192_px_under_the_same_name(self):
        d = tempfile.mkdtemp(); write(d, 'photos/journey_pictures.json', {}); write(d, 'data/journeys/config.json', {'couple': 1, 'src': {}})
        write(d, 'data/journeys/knot.json', {'pos': 0, 'id': 'knot', 'type': 'species', 'title': 'T', 'text': 't', 'imgwiki': 'Red knot', 'ends': []})
        def find(todo):
            for u in todo: yield u, ss.Res('found', row(), jpeg((330, 220)), note='S.jpg')
        w = jj.Photos(d); sj.acquire(w, jj.load_units(d), [('wikipedia', find, lambda w, u: True, None)], log=lambda m: None, copies=lambda e, need=('large',), get=None: sj.make_copies(e, ('large',), lambda u, raw=False: jpeg((1000, 500))))
        w = jj.Photos(d); self.assertEqual(w.pics['knot']['f'], 'knot.webp'); self.assertEqual(max(size_of(os.path.join(d, 'photos/journeys/knot.webp'))), 192)
        self.assertEqual(max(size_of(os.path.join(d, 'photos/journeys-lg/knot.webp'))), 400); self.assertEqual(w.check(), [])


class OldShapeKeepsWorking(unittest.TestCase):
    def test_old_species_files_and_lists_validate_and_repair_changes_nothing(self):
        d = old_species_root(); w = sp.SpeciesPhotos(d); self.assertEqual(w.check(), []); self.assertEqual(w.repair(), [])

    def test_old_journey_files_validate(self):
        self.assertEqual(jp.JourneyPhotos(old_journey_root()).check(), [])

    def test_the_build_payload_reads_a_192_px_journey_cover_and_an_old_96_px_one_from_the_same_path(self):
        d = old_journey_root(); w = jp.JourneyPhotos(d); self.assertEqual({e['f'] for e in w.pics.values()}, {'osprey.webp', 'knot.webp', 'big.webp'})
        self.assertEqual({k: max(size_of(os.path.join(d, 'photos/journeys', e['f']))) for k, e in w.pics.items()}, {'osprey': 96, 'knot': 96, 'big': 192})


class Migration(unittest.TestCase):
    def test_species_dry_run_lists_the_right_files_and_writes_nothing(self):
        d = old_species_root(); before = sorted((r, f) for r, _, fs in os.walk(d) for f in fs); out = []
        self.assertEqual(drop96px.main(['--kind', 'species', '--dry'], root=d, out=lambda *a: out.append(' '.join(map(str, a)))), 0)
        self.assertIn('3 96 px files would be deleted', out[0]); self.assertIn('2 192 px copies made', out[0]); self.assertIn('1 96 px files stay', out[0])
        r = sp.SpeciesPhotos(d).migrate_192(dry=True)
        self.assertEqual(sorted(r['delete']), ['photos/species/aaaaaaaaaaaa.webp', 'photos/species/bbbbbbbbbbbb.webp', 'photos/species/dddddddddddd.webp'])
        self.assertEqual(sorted(r['made']), ['bb', 'ee']); self.assertEqual(list(r['kept']), ['cccccccccccc.webp'])
        self.assertEqual(before, sorted((rr, f) for rr, _, fs in os.walk(d) for f in fs))

    def test_species_migration_makes_192_from_400_deletes_96_and_keeps_everything_consistent(self):
        d = old_species_root(); self.assertEqual(drop96px.main(['--kind', 'species'], root=d, out=lambda *a: None), 0)
        w = sp.SpeciesPhotos(d); self.assertEqual(w.check(), [])
        self.assertEqual(sorted(os.listdir(os.path.join(d, 'photos/species'))), ['cccccccccccc.webp'], 'only the picture with nothing to make a 192 px copy from keeps its 96 px file')
        self.assertEqual(max(size_of(os.path.join(d, 'photos/species-md/bbbbbbbbbbbb.webp'))), 192)
        self.assertEqual(w.medium, {'aa': 'aaaaaaaaaaaa.webp', 'bb': 'bbbbbbbbbbbb.webp', 'dd': 'dddddddddddd.webp', 'ee': 'dddddddddddd.webp'})
        self.assertEqual(w.pics['bb']['f'], 'bbbbbbbbbbbb.webp', 'the credit rows and their f names do not change')
        self.assertEqual(drop96px.main(['--kind', 'species'], root=d, out=lambda *a: None), 0); self.assertEqual(sp.SpeciesPhotos(d).migrate_192(dry=True), {'delete': [], 'made': [], 'kept': {'cccccccccccc.webp': 'no 192 px copy and no 400 px copy to make it from (cc)'}})

    def test_journey_dry_run_and_migration(self):
        d = old_journey_root(); r = jp.JourneyPhotos(d).migrate_192(dry=True)
        self.assertEqual(r['made'], ['osprey']); self.assertEqual(list(r['kept']), ['knot']); self.assertEqual(max(size_of(os.path.join(d, 'photos/journeys/osprey.webp'))), 96)
        self.assertEqual(drop96px.main(['--kind', 'journeys'], root=d, out=lambda *a: None), 0)
        self.assertEqual(max(size_of(os.path.join(d, 'photos/journeys/osprey.webp'))), 192); self.assertEqual(max(size_of(os.path.join(d, 'photos/journeys/knot.webp'))), 96)
        self.assertEqual(jp.JourneyPhotos(d).check(), []); self.assertEqual(jp.JourneyPhotos(d).migrate_192(dry=True)['made'], [])


if __name__ == '__main__': unittest.main()
