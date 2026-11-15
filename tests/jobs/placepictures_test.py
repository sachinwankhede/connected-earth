#!/usr/bin/env python3
"""jobs/placepictures.py: the one acquire job for place pictures. Fake sources only: no network."""
import datetime, io, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import placepictures as pj, place_photos as pp, authorlookup as al, commonsplacephotos as cpp

def jpeg():
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', (40, 30), (20, 90, 40)).save(b, 'JPEG'); return b.getvalue()

def row(pid, a='Jane Doe', l='CC BY 4.0'):
    return dict(f=pid + '.jpg', a=a, l=l, lu='https://creativecommons.org/licenses/by/4.0/', p='https://commons.wikimedia.org/wiki/File:Some_file.jpg', w='https://en.wikipedia.org/wiki/Some',
                checkedAt='2026-11-15T00:00:00+00:00', fetchedAt='2026-11-15T00:00:00+00:00')

def unit(pid, title=None): return dict(id=pid, title=title or pid.title(), name=pid.title(), short='', lat=1.0, lon=2.0, place='Maine, USA', region='Maine, USA')

def strategy(name, found=(), miss=(), offered=None, entry=None):
    """A fake source: finds the places in `found`, gives nothing for those in `miss`; records which places it was offered."""
    def find(todo):
        for u in todo:
            if offered is not None: offered.append((name, u['id']))
            if u['id'] in found: yield u, pj.Res('found', (entry or row)(u['id']), jpeg(), note='file.jpg')
            elif u['id'] in miss: yield u, pj.Res('miss', why='nothing', status='nophoto')
    return (name, find, lambda w, u: name == 'wikipedia' or w.is_missing(u['id']), None if name == 'wikipedia' else 90)

class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.w = pp.PlacePhotos(self.d); self.log = []; self._lookup = al.lookup
    def tearDown(self): al.lookup = self._lookup
    def run_(self, strategies, units, **kw): return pj.acquire(self.w, units, strategies, log=self.log.append, **kw)
    def fresh(self): return pp.PlacePhotos(self.d)

    def test_the_first_strategy_that_accepts_a_picture_wins_and_later_ones_are_not_asked(self):
        offered = []; units = [unit('aa'), unit('bb')]
        stats, stopped = self.run_([strategy('wikipedia', found={'aa'}, miss={'bb'}, offered=offered), strategy('commons', found={'aa', 'bb'}, offered=offered)], units)
        self.assertEqual(offered, [('wikipedia', 'aa'), ('wikipedia', 'bb'), ('commons', 'bb')], 'aa has its picture, so commons is only asked about bb')
        w = self.fresh(); self.assertEqual(sorted(w.pics), ['aa', 'bb']); self.assertEqual(w.check(), []); self.assertEqual(stopped, [])
        self.assertEqual((stats['wikipedia']['found'], stats['commons']['found']), (1, 1))

    def test_rows_are_keyed_by_place_id_with_the_title_and_measured_fields(self):
        self.run_([strategy('wikipedia', found={'aa'})], [unit('aa', 'Arrowhead Lake')])
        w = self.fresh(); r = w.pics['aa']
        self.assertEqual((r['f'], r['wiki']), ('aa.jpg', 'Arrowhead Lake')); self.assertEqual((r['mt'], r['width'], r['height']), ('image/jpeg', 40, 30))
        self.assertEqual(len(r['sha256']), 64); self.assertEqual(r['reviewStatus'], 'approved'); self.assertTrue(os.path.exists(os.path.join(self.d, 'photos/places/aa.jpg')))
        self.assertFalse(w.is_missing('aa'))

    def test_a_cc_by_picture_without_an_author_is_refused_unless_commons_names_one(self):
        unknown = lambda pid: row(pid, a='Unknown author')
        al.lookup = lambda fn: ('none', '')
        self.run_([strategy('wikipedia', found={'aa'}, entry=unknown), strategy('commons', found={'aa'}, entry=unknown)], [unit('aa')])
        w = self.fresh(); self.assertFalse(w.has('aa')); self.assertEqual(w.miss_['aa']['status'], 'notfree'); self.assertEqual(sorted(w.tried['aa']), ['commons', 'wikipedia'])
        self.assertTrue(any(l.startswith('refused wikipedia aa') and 'no author' in l for l in self.log))
        al.lookup = lambda fn: ('artist', 'Pat Smith'); self.w = self.fresh()
        self.run_([strategy('commons', found={'aa'}, entry=unknown)], [unit('aa')], again=True)
        self.assertEqual(self.fresh().pics['aa']['a'], 'Pat Smith', 'the name Commons gives is stored, not "Unknown author"')

    def test_cc0_and_public_domain_need_no_author(self):
        al.lookup = lambda fn: self.fail('no lookup for a licence that needs no author')
        self.run_([strategy('wikipedia', found={'aa'}, entry=lambda pid: row(pid, a='Unknown author', l='CC0'))], [unit('aa')])
        self.assertTrue(self.fresh().has('aa'))

    def test_vetted_info_lets_the_strategy_take_the_next_file(self):
        al.lookup = lambda fn: ('none', '') if fn == 'A.jpg' else ('artist', 'X')
        thumb = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/%s/330px-%s'
        info = {n: ('CC BY-SA 4.0', 'Unknown' if n == 'A.jpg' else 'Real Author', 'https://creativecommons.org/licenses/by-sa/4.0/', thumb % (n, n), 'image/jpeg') for n in ('A.jpg', 'B.jpg')}
        got = cpp.pick(['A.jpg', 'B.jpg'], pj.Vetted(info))
        self.assertEqual((got[0], got[2]), ('B.jpg', 'Real Author'), 'A has no author to be found: B is taken')
        al.lookup = lambda fn: ('attribution', 'Stan Shebs')
        self.assertEqual(cpp.pick(['A.jpg'], pj.Vetted(info))[2], 'Stan Shebs')

    def test_holds_are_the_old_jobs_holds(self):
        today = datetime.date(2026, 11, 15); w = self.w; offered = []
        for pid in ('hold', 'old', 'free', 'fresh_miss'): w.miss(pid, 'nophoto', 'wikipedia')
        w.tried['hold']['commons'] = (today - datetime.timedelta(days=10)).isoformat(); w.tried['old']['commons'] = (today - datetime.timedelta(days=91)).isoformat()
        w.miss_['fresh_miss'] = pp.pr.negative_entry('nophoto', 1); w.miss_['hold'] = pp.pr.negative_entry('nophoto', 1, datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc))
        units = [unit(p) for p in ('hold', 'old', 'free', 'fresh_miss')]
        self.run_([strategy('wikipedia', offered=offered), strategy('commons', offered=offered)], units, today=today)
        self.assertEqual(sorted(p for n, p in offered if n == 'commons'), ['free', 'fresh_miss', 'old'], 'commons: held 90 days from its date; "hold" was tried 10 days ago')
        self.assertEqual([p for n, p in offered if n == 'wikipedia'], ['hold'], 'wikipedia: held while the missing record has not expired; only the expired one is tried again')
        offered.clear(); self.run_([strategy('commons', offered=offered)], units, today=today, again=True)
        self.assertEqual(sorted(p for n, p in offered), ['free', 'fresh_miss', 'hold', 'old'], '--again ignores the hold')

    def test_a_source_that_found_nothing_is_noted_in_the_ledger_only(self):
        self.w.miss('aa', 'notphoto', 'wikipedia'); self.w.commit(); self.w = self.fresh(); before = self.w.miss_['aa']
        self.run_([strategy('commons', miss={'aa'})], [unit('aa')])
        w = self.fresh(); self.assertEqual(w.miss_['aa'], before); self.assertEqual(w.tried['aa']['commons'], datetime.date.today().isoformat())

    def test_a_run_that_changes_nothing_writes_no_file(self):
        self.w.put('aa', dict(row('aa'), wiki='Aa'), jpeg()); self.w.miss('bb', 'nophoto', 'wikipedia'); self.w.note_tried('bb', 'commons'); self.w.commit()
        files = lambda: {os.path.join(r, f): open(os.path.join(r, f), 'rb').read() for r, _, fs in os.walk(self.d) for f in fs}
        before = files(); self.w = self.fresh()
        self.run_([strategy('wikipedia', miss={'cc'}), strategy('commons', found={'bb'})], [unit('aa'), unit('bb')], today=datetime.date.today())
        self.assertEqual(files(), before, 'aa has a picture and bb is held: nothing is offered, nothing is written')
        # a run that only notes a ledger date rewrites the lists in the same layout: the picture lists stay byte-identical
        self.w = self.fresh(); self.run_([strategy('commons', miss={'bb'})], [unit('bb')], again=True); after = files()
        for rel in ('photos/places/places.json', 'photos/places/missing.json', 'photos/places_large.json'):
            self.assertEqual(after[os.path.join(self.d, rel)], before[os.path.join(self.d, rel)], rel)

    def test_the_byte_cap_stops_the_run_and_what_was_kept_is_saved(self):
        stats, _ = self.run_([strategy('wikipedia', found={'aa', 'bb', 'cc'})], [unit('aa'), unit('bb'), unit('cc')], max_bytes=1)
        self.assertEqual(stats['wikipedia']['found'], 1); self.assertEqual(sorted(self.fresh().pics), ['aa']); self.assertTrue(any(l.startswith('STOP') for l in self.log))

    def test_a_source_that_stops_is_reported_and_the_rest_carries_on(self):
        def boom(todo):
            raise RuntimeError('three requests in a row failed')
            yield
        stats, stopped = self.run_([('openverse', boom, lambda w, u: True, 90), strategy('wikipedia', found={'aa'})], [unit('aa')])
        self.assertEqual(stopped, ['openverse']); self.assertTrue(self.fresh().has('aa'))

    def test_dry_run_writes_nothing(self):
        self.run_([strategy('wikipedia', found={'aa'}, miss={'bb'})], [unit('aa'), unit('bb')], dry=True)
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos'))); self.assertTrue(any(l.startswith('yes wikipedia aa') for l in self.log))

class UnitsTests(unittest.TestCase):
    def test_places_with_a_shared_title_are_skipped(self):
        d = tempfile.mkdtemp()
        for pid, t in (('aa', 'Gulf'), ('bb', 'Gulf'), ('cc', 'Cedar'), ('dd', None)):
            json.dump(dict(id=pid, name=pid, imgwiki=t, place='Maine, USA', lat=1, lon=2) if t else dict(id=pid, name=pid), open(os.path.join(d, pid + '.json'), 'w'))
        json.dump({'order': []}, open(os.path.join(d, 'order.json'), 'w'))
        units, shared = pj.load_units(d)
        self.assertEqual([u['id'] for u in units], ['cc']); self.assertEqual([u['id'] for u in shared], ['aa', 'bb'])

class MainTests(unittest.TestCase):
    def test_title_keyed_files_are_refused_until_the_migration_has_run(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'photos', 'places')); os.makedirs(os.path.join(d, 'data', 'places'))
        json.dump({'Some title': dict(f='x.jpg')}, open(os.path.join(d, 'photos/places/places.json'), 'w'))
        out = io.StringIO(); old = sys.stdout; sys.stdout = out
        try: code = pj.main([], root=d)
        finally: sys.stdout = old
        self.assertEqual(code, 1); self.assertIn('migration', out.getvalue())

if __name__ == '__main__': unittest.main()
