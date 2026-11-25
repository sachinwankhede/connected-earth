#!/usr/bin/env python3
"""jobs/speciespictures.py: the one acquire job for species pictures. Fake sources only: no network. Everything runs in a temp root in the NEW (sid-keyed) shape."""
import datetime, io, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import speciespictures as sj, species_photos as sp, species_sources as ss, author_lookup as al

def jpeg(color=(20, 90, 40), size=(300, 200)):
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', size, color).save(b, 'JPEG'); return b.getvalue()

def row(sid, a='Jane Doe', l='CC BY 4.0', u='a/ab/Some_file.jpg/330px-Some_file.jpg'):
    return dict(a=a, l=l, lu='https://creativecommons.org/licenses/by/4.0/', p='https://commons.wikimedia.org/wiki/File:Some_file.jpg', page='Some', u=u)

def unit(sid, title=None, abiotic=False): return dict(sid=sid, title=title or sid.title(), name=sid.title(), latin=sid.title(), abiotic=abiotic)

def strategy(name, found=(), miss=(), offered=None, entry=None):
    """A fake source: finds the species whose sid is in `found`, gives nothing for those in `miss`; records which titles it was offered."""
    def find(todo):
        for u in todo:
            if offered is not None: offered.append((name, u['sid']))
            if u['sid'] in found: yield u, ss.Res('found', (entry or row)(u['sid']), jpeg((sum(map(ord, u['sid'])) % 256, 90, 40)), note='file.jpg')
            elif u['sid'] in miss: yield u, ss.Res('miss', why='nothing', status='nophoto')
    return (name, find, lambda w, u: name == 'wikipedia' or w.is_missing(u['sid']), None if name == 'wikipedia' else 90)

def fake_copies(entry, need=('medium', 'large'), log=None):
    if log is not None: log.append(entry['f'] if 'f' in entry else entry.get('u'))
    return {k: b'COPY-' + k.encode() for k in need}, ''

def new_root():
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'photos')); json.dump({}, open(os.path.join(d, 'photos', 'species_pictures.json'), 'w')); return d

class AcquireTests(unittest.TestCase):
    def setUp(self): self.d = new_root(); self.w = sp.SpeciesPhotos(self.d); self.log = []; self._lookup = al.lookup
    def tearDown(self): al.lookup = self._lookup
    def run_(self, strategies, units, **kw): return sj.acquire(self.w, units, strategies, log=self.log.append, **kw)
    def fresh(self): return sp.SpeciesPhotos(self.d)

    def test_the_first_strategy_that_accepts_a_picture_wins_and_later_ones_are_not_asked(self):
        offered = []; units = [unit('aa'), unit('bb')]
        stats, stopped = self.run_([strategy('wikipedia', found={'aa'}, miss={'bb'}, offered=offered), strategy('commons', found={'aa', 'bb'}, offered=offered)], units)
        self.assertEqual(offered, [('wikipedia', 'aa'), ('wikipedia', 'bb'), ('commons', 'bb')])
        w = self.fresh(); self.assertEqual(sorted(w.pics), ['aa', 'bb']); self.assertEqual(w.check(), []); self.assertEqual(stopped, [])
        self.assertEqual((stats['wikipedia']['found'], stats['commons']['found']), (1, 1)); self.assertEqual(w.pics['aa']['wiki'], 'Aa')

    def test_the_default_order_is_wikipedia_commons_gbif_openverse_inaturalist(self):
        self.assertEqual([s[0] for s in sj.STRATEGIES], ['wikipedia', 'commons', 'gbif', 'openverse', 'inaturalist'])

    def test_a_cc_by_picture_without_an_author_is_refused_unless_commons_names_one(self):
        unknown = lambda sid: row(sid, a='Unknown author')
        al.lookup = lambda fn: ('none', '')
        self.run_([strategy('wikipedia', found={'aa'}, entry=unknown), strategy('commons', found={'aa'}, entry=unknown)], [unit('aa')])
        w = self.fresh(); self.assertFalse(w.has('aa')); self.assertEqual(w.miss_['aa']['status'], 'notfree'); self.assertEqual(sorted(w.tried['aa']), ['commons', 'wikipedia'])
        self.assertTrue(any(l.startswith('refused wikipedia') and 'no author' in l for l in self.log))
        al.lookup = lambda fn: ('artist', 'Pat Smith'); self.w = self.fresh()
        self.run_([strategy('commons', found={'aa'}, entry=unknown)], [unit('aa')], again=True)
        self.assertEqual(self.fresh().pics['aa']['a'], 'Pat Smith')

    def test_the_writer_refusing_an_author_is_recorded_as_tried_not_a_crash(self):
        al.lookup = lambda fn: ('artist', 'x')
        # vet lets this through (a name is there), the writer's own rule refuses it: the licence says CC BY and the cleaned author is empty
        self.w.miss('aa', 'nophoto', 'wikipedia'); orig = sp.author_missing; sp.author_missing = lambda e: True
        try: self.run_([strategy('commons', found={'aa'})], [unit('aa')])
        finally: sp.author_missing = orig
        w = self.fresh(); self.assertFalse(w.has('aa')); self.assertIn('commons', w.tried['aa']); self.assertTrue(any(l.startswith('refused commons aa') for l in self.log))

    def test_cc0_still_needs_an_author(self):   # owner, 25 Nov (#887): every picture needs a named author, whatever its licence, so CC0 with no author is refused too
        al.lookup = lambda fn: ('none', '')
        self.run_([strategy('wikipedia', found={'aa'}, entry=lambda sid: row(sid, a='Unknown author', l='CC0'))], [unit('aa')])
        self.assertFalse(self.fresh().has('aa'))

    def test_holds_are_the_old_jobs_holds(self):
        today = datetime.date(2026, 11, 15); w = self.w; offered = []
        for sid in ('hold', 'old', 'free', 'fresh_miss'): w.miss(sid, 'nophoto', 'wikipedia')
        w.tried['hold']['commons'] = (today - datetime.timedelta(days=10)).isoformat(); w.tried['old']['commons'] = (today - datetime.timedelta(days=91)).isoformat()
        w.miss_['fresh_miss'] = sp.pr.negative_entry('nophoto', 1); w.miss_['hold'] = sp.pr.negative_entry('nophoto', 1, datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc))
        units = [unit(s) for s in ('hold', 'old', 'free', 'fresh_miss')]
        self.run_([strategy('wikipedia', offered=offered), strategy('commons', offered=offered)], units, today=today)
        self.assertEqual(sorted(s for n, s in offered if n == 'commons'), ['free', 'fresh_miss', 'old'])
        self.assertEqual([s for n, s in offered if n == 'wikipedia'], ['hold'], 'only the expired missing record is tried again')
        offered.clear(); self.run_([strategy('commons', offered=offered)], units, today=today, again=True)
        self.assertEqual(sorted(s for n, s in offered), ['free', 'fresh_miss', 'hold', 'old'])

    def test_a_source_that_found_nothing_is_noted_in_the_ledger_only(self):
        self.w.miss('aa', 'notphoto', 'wikipedia'); self.w.commit(); self.w = self.fresh(); before = self.w.miss_['aa']
        self.run_([strategy('commons', miss={'aa'})], [unit('aa')])
        w = self.fresh(); self.assertEqual(w.miss_['aa'], before); self.assertEqual(w.tried['aa']['commons'], datetime.date.today().isoformat())

    def test_abiotic_titles_are_not_offered_to_openverse_or_inaturalist(self):
        offered = []; self.w.miss('rain', 'nophoto', 'wikipedia'); self.w.miss('wolf', 'nophoto', 'wikipedia')
        for n in ('openverse', 'inaturalist'):
            s = list(ss.SOURCES[[x[0] for x in ss.SOURCES].index(n)])
            def find(todo, n=n):
                for u in todo: offered.append((n, u['sid'])); yield u, ss.Res('miss', why='x')
            s[1] = find; self.run_([tuple(s)], [unit('rain', abiotic=True), unit('wolf')])
        self.assertEqual(sorted(offered), [('inaturalist', 'wolf'), ('openverse', 'wolf')])

    def test_a_title_shared_by_several_species_is_fetched_once_and_each_sid_gets_its_own_entry(self):
        offered = []; units = [unit('rain1', 'Rain'), unit('rain2', 'Rain'), unit('wolf', 'Wolf')]
        stats, _ = self.run_([strategy('wikipedia', found={'rain1', 'wolf'}, offered=offered)], units, copies=fake_copies)
        self.assertEqual(sorted(offered), [('wikipedia', 'rain1'), ('wikipedia', 'wolf')], 'one fetch for the title Rain')
        w = self.fresh(); self.assertEqual(sorted(w.pics), ['rain1', 'rain2', 'wolf']); self.assertEqual(w.check(), [])
        self.assertEqual(w.pics['rain1']['f'], w.pics['rain2']['f']); self.assertNotEqual(w.pics['rain1']['f'], w.pics['wolf']['f'], 'a different picture, a different file')
        self.assertEqual((w.pics['rain1']['wiki'], w.pics['rain2']['wiki']), ('Rain', 'Rain')); self.assertEqual(stats['wikipedia']['found'], 3)
        self.assertTrue(w.has_medium('rain2') and w.has_large('rain2')); self.assertEqual(sorted(os.listdir(os.path.join(self.d, 'photos/species'))).__len__(), 2)

    def test_a_shared_title_with_no_picture_is_recorded_for_every_sid(self):
        self.run_([strategy('wikipedia', miss={'rain1'})], [unit('rain1', 'Rain'), unit('rain2', 'Rain')])
        w = self.fresh(); self.assertEqual(sorted(w.miss_), ['rain1', 'rain2'])

    def test_copies_are_made_in_the_same_commit_as_the_picture(self):
        made = []
        self.run_([strategy('wikipedia', found={'aa'})], [unit('aa')], copies=lambda e, need=('medium', 'large'): fake_copies(e, need, made))
        w = self.fresh(); self.assertTrue(w.has('aa') and w.has_medium('aa') and w.has_large('aa')); self.assertEqual(w.check(), [])
        f = w.pics['aa']['f']
        self.assertEqual(open(os.path.join(self.d, 'photos/species-md', f), 'rb').read(), b'COPY-medium'); self.assertEqual(open(os.path.join(self.d, 'photos/species-lg', f), 'rb').read(), b'COPY-large')

    def test_a_picture_is_kept_alone_when_no_copy_can_be_made(self):
        stats, _ = self.run_([strategy('wikipedia', found={'aa'})], [unit('aa')], copies=lambda e, need=('medium', 'large'): ({}, 'the source has no thumbnail for it'))
        w = self.fresh(); self.assertTrue(w.has('aa')); self.assertFalse(w.has_large('aa')); self.assertFalse(w.has_medium('aa')); self.assertEqual(w.check(), [])
        self.assertEqual(stats['wikipedia']['nocopy'], 1); self.assertTrue(any('small picture stays' in l for l in self.log))

    def test_strategies_medium_and_large_fill_only_the_gaps_and_add_no_pictures(self):
        self.w.put('aa', dict(row('aa'), wiki='Aa'), jpeg()); self.w.put('bb', dict(row('bb'), wiki='Bb'), jpeg((200, 0, 0))); self.w.put('gb', dict(row('gb', u='gbif/123'), wiki='G'), jpeg((0, 0, 200)))
        self.w.put_large('aa', b'OLD'); self.w.commit(); self.w = self.fresh(); asked = []; found = []
        def copies(e, need=('medium', 'large')): asked.append((e['wiki'], need)); return {k: b'NEW' for k in need}, ''
        self.run_([strategy('wikipedia', found={'cc'}, offered=found)], [unit('aa'), unit('bb'), unit('cc')], copies=copies, only='large')
        w = self.fresh(); self.assertEqual(asked, [('Bb', ('large',))]); self.assertEqual(found, [], 'no picture strategy is asked'); self.assertEqual(sorted(w.pics), ['aa', 'bb', 'gb'])
        self.assertTrue(w.has_large('bb')); self.assertFalse(w.has_medium('bb')); self.assertFalse(w.has_large('gb'), 'a GBIF picture has no source address for a copy')
        asked.clear(); self.w = self.fresh(); self.run_([], [], copies=copies, only='medium'); self.assertEqual(sorted(a[0] for a in asked), ['Aa', 'Bb']); self.assertEqual(self.fresh().check(), [])

    def test_a_run_that_changes_nothing_writes_no_file_and_dry_writes_nothing(self):
        self.w.put('aa', dict(row('aa'), wiki='Aa'), jpeg()); self.w.put_medium('aa', b'M'); self.w.put_large('aa', b'L'); self.w.commit()
        files = lambda: {os.path.join(r, f): open(os.path.join(r, f), 'rb').read() for r, _, fs in os.walk(self.d) for f in fs}
        before = files(); self.w = self.fresh()
        self.run_([strategy('wikipedia', miss={'bb'})], [unit('aa')], copies=fake_copies); self.assertEqual(files(), before)
        self.w = self.fresh(); self.run_([strategy('wikipedia', found={'bb'}, miss={'cc'})], [unit('bb'), unit('cc')], dry=True, copies=fake_copies)
        self.assertEqual(files(), before); self.assertTrue(any(l.startswith('yes wikipedia') for l in self.log))
        self.w = self.fresh(); self.run_([], [unit('aa')], dry=True, copies=fake_copies, only='all'); self.assertEqual(files(), before)

    def test_the_byte_cap_stops_the_run_and_what_was_kept_is_saved(self):
        stats, _ = self.run_([strategy('wikipedia', found={'aa', 'bb', 'cc'})], [unit('aa'), unit('bb'), unit('cc')], max_bytes=1)
        self.assertEqual(stats['wikipedia']['found'], 1); self.assertEqual(sorted(self.fresh().pics), ['aa']); self.assertTrue(any(l.startswith('STOP') for l in self.log))

    def test_a_source_that_stops_is_reported_and_the_rest_carries_on(self):
        def boom(todo):
            raise RuntimeError('three requests in a row failed')
            yield
        stats, stopped = self.run_([('openverse', boom, lambda w, u: True, 90), strategy('wikipedia', found={'aa'})], [unit('aa')])
        self.assertEqual(stopped, ['openverse']); self.assertTrue(self.fresh().has('aa'))

class UnitsAndMainTests(unittest.TestCase):
    def rows(self, d, specs):
        for sid, wiki, cat in specs:
            p = os.path.join(d, 'data/species/rows', sid[:2]); os.makedirs(p, exist_ok=True)
            json.dump(dict(sid=sid, latin=sid.title(), name=sid.title(), wiki=wiki, **({'cat': cat} if cat else {})), open(os.path.join(p, sid + '.json'), 'w'))

    def test_units_one_per_row_and_abiotic_follows_the_title(self):
        d = tempfile.mkdtemp(); self.rows(d, [('rain', 'Rain', 'abiotic'), ('rainx', 'Rain', None), ('wolf', 'Wolf', None), ('nowiki', None, None)])
        u = sj.load_units(d); self.assertEqual([x['sid'] for x in u], ['rain', 'rainx', 'wolf']); self.assertEqual([x['abiotic'] for x in u], [True, True, False])

    def test_title_keyed_files_are_refused_until_the_migration_has_run(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'photos'))
        out = io.StringIO(); old = sys.stdout; sys.stdout = out
        try: code = sj.main([], root=d)
        finally: sys.stdout = old
        self.assertEqual(code, 1); self.assertIn('migration', out.getvalue())

    def test_unknown_strategy_and_a_stopped_source_exit_codes(self):
        d = new_root(); self.rows(d, [('aa', 'Aa', None)]); cwd = os.getcwd(); os.chdir(d); old = sys.stdout; sys.stdout = io.StringIO()
        saved = sj.STRATEGIES
        try:
            self.assertEqual(sj.main(['--strategy', 'nope'], root=d), 1)
            def boom(todo):
                raise RuntimeError('refused')
                yield
            sj.STRATEGIES = [('wikipedia', boom, lambda w, u: True, None)]
            self.assertEqual(sj.main(['--strategy', 'wikipedia'], root=d), 2); self.assertTrue(os.path.exists('speciespictures_stats.md'))
        finally: sj.STRATEGIES = saved; sys.stdout = old; os.chdir(cwd)

class SourceHelperTests(unittest.TestCase):
    def test_source_addresses_follow_the_source_of_the_picture(self):
        self.assertEqual(ss.source_urls('gbif/1'), []); self.assertEqual(ss.source_urls(None), [])
        self.assertEqual(ss.source_urls('openverse/abc'), ['https://api.openverse.org/v1/images/abc/thumb/'])
        self.assertEqual(ss.source_urls('inaturalist/5'), ['https://inaturalist-open-data.s3.amazonaws.com/photos/5/medium.jpg'])
        c = ss.source_urls('a/ab/Wolf.jpg/330px-Wolf.jpg'); self.assertEqual(c, [ss.BASE + 'a/ab/Wolf.jpg/500px-Wolf.jpg', ss.BASE + 'a/ab/Wolf.jpg/330px-Wolf.jpg'])
        self.assertEqual(ss.commons_file('a/ab/Wolf%20x.jpg/330px-Wolf.jpg'), 'Wolf x.jpg')

    def test_copy_sizes(self):
        from PIL import Image
        got, why = sj.make_copies(dict(u='a/ab/W.jpg/330px-W.jpg'), get=lambda u, raw=False: jpeg(size=(1000, 500)))
        self.assertEqual(why, ''); self.assertEqual(Image.open(io.BytesIO(got['medium'])).size, (192, 96)); self.assertEqual(Image.open(io.BytesIO(got['large'])).size, (400, 200))
        def bad(u, raw=False): raise RuntimeError('HTTP 400')
        self.assertEqual(sj.make_copies(dict(u='a/ab/W.jpg/330px-W.jpg'), get=bad)[0], {}); self.assertEqual(sj.make_copies(dict(u='gbif/1'))[0], {})
        self.assertEqual(sj.make_copies(dict(u='a/ab/W.jpg/330px-W.jpg'), get=lambda u, raw=False: b'x')[0], {})
        self.assertEqual(list(sj.make_copies(dict(u='a/ab/W.jpg/330px-W.jpg'), need=('large',), get=lambda u, raw=False: jpeg())[0]), ['large'])

    def test_candidate_rules_carry_over(self):
        self.assertEqual(ss.gbif_licence_of({'license': 'CC_BY_4_0'})[0], 'CC BY 4.0'); self.assertIsNone(ss.gbif_licence_of({'license': 'http://creativecommons.org/licenses/by-nc/4.0/'}))
        self.assertEqual(ss.match_taxon([{'name': 'Canis lupus', 'rank': 'species', 'id': 7}], 'canis lupus'), 7); self.assertIsNone(ss.match_taxon([{'name': 'Canis lupus', 'rank': 'subspecies', 'id': 7}], 'Canis lupus'))
        self.assertEqual(ss.inat_name(dict(title='Gray_wolf', name='Gray wolf', latin='Canis lupus')), 'Canis lupus'); self.assertEqual(ss.inat_name(dict(title='Canis lupus', name='Gray wolf', latin='Canis lupus')), 'Canis lupus')
        self.assertEqual(ss.inat_name(dict(title='Gray wolf', name='Gray wolf', latin='Canis lupus lupus')), 'Gray wolf', 'a subspecies would show the species photos')
        cs_ = ss.inat_candidates({'taxon_photos': [{'photo': {'id': 5, 'license_code': 'cc-by', 'attribution_name': 'A B', 'medium_url': ss.INAT_BUCKET + '5/medium.jpg'}},
                                                   {'photo': {'id': 6, 'license_code': 'cc-by-nc', 'attribution_name': 'A B', 'medium_url': ss.INAT_BUCKET + '6/medium.jpg'}}]})
        self.assertEqual([c[0] for c in cs_], [5])

if __name__ == '__main__': unittest.main()
