#!/usr/bin/env python3
"""jobs/journeypictures.py: the journey strategy of the acquire job. Fake sources only: no network. Everything runs in a temp root in the journey-id-keyed shape."""
import io, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import journeypictures as jj, speciespictures as sj, journey_photos as jp, species_sources as ss, author_lookup as al

def jpeg(color=(20, 90, 40), size=(300, 200)):
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', size, color).save(b, 'JPEG'); return b.getvalue()

def put(d, rel, obj):
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

def tree(journeys):
    """A root with photos/journey_pictures.json (the migration has run) and one data/journeys file per (id, type, imgwiki)."""
    d = tempfile.mkdtemp(); put(d, 'photos/journey_pictures.json', {}); put(d, 'data/journeys/config.json', {'couple': 1, 'src': {}})
    for jid, typ, img in journeys: put(d, 'data/journeys/%s.json' % jid, {'pos': 0, 'id': jid, 'type': typ, 'title': 'T', 'text': 't', 'imgwiki': img, 'ends': []})
    return d

def row(jid, a='Jane Doe', l='CC BY 4.0'):
    return dict(a=a, l=l, lu='https://creativecommons.org/licenses/by/4.0/', p='https://commons.wikimedia.org/wiki/File:Some_file.jpg', page='Some', u='a/ab/Some_file.jpg/330px-Some_file.jpg')

def strategy(name, found=(), offered=None, entry=None, miss_why='nothing', applies=None):
    """A fake source over titles: finds the journeys (by id) in `found`; the applies rule is the job's own for that name."""
    def find(todo):
        for u in todo:
            if offered is not None: offered.append((name, u['sid']))
            if u['sid'] in found: yield u, ss.Res('found', (entry or row)(u['sid']), jpeg(), note='file.jpg')
            else: yield u, ss.Res('miss', why=miss_why, status='nophoto')
    rule = [s for s in jj.STRATEGIES if s[0] == name][0]
    return (name, find, rule[2], rule[3])

def fake_copies(entry, need=('large',)): return ({'large': b'LARGE'} if 'large' in need else {}), ''

class JourneyAcquireTests(unittest.TestCase):
    def setUp(self):
        self.d = tree([('osprey', 'species', 'Osprey'), ('chesosprey', 'species', 'Osprey'), ('dust', 'flow', 'Saharan Air Layer'), ('knot', 'species', 'Red knot')])
        self.w = jj.Photos(self.d); self.units = jj.load_units(self.d); self.log = []; self._lookup = al.lookup
    def tearDown(self): al.lookup = self._lookup
    def run_(self, strategies, **kw): return sj.acquire(self.w, self.units, strategies, log=self.log.append, copies=kw.pop('copies', fake_copies), **kw)
    def fresh(self): return jj.Photos(self.d)

    def test_units_are_the_journeys_with_their_imgwiki_and_flow_journeys_are_abiotic(self):
        self.assertEqual([(u['sid'], u['title'], u['abiotic']) for u in self.units], [('chesosprey', 'Osprey', False), ('dust', 'Saharan Air Layer', True), ('knot', 'Red knot', False), ('osprey', 'Osprey', False)])

    def test_a_title_shared_by_two_journeys_is_fetched_once_and_each_gets_its_own_row_file_and_larger_copy(self):
        offered = []
        self.run_([strategy('wikipedia', found={'chesosprey'}, offered=offered)])
        self.assertEqual([o for o in offered if o[1] in ('chesosprey', 'osprey')], [('wikipedia', 'chesosprey')])
        w = self.fresh(); self.assertEqual(sorted(w.pics), ['chesosprey', 'osprey']); self.assertEqual(w.check(), [])
        self.assertEqual(sorted(w.large), ['chesosprey', 'osprey']); self.assertTrue(os.path.isfile(os.path.join(self.d, 'photos', 'journeys', 'osprey.webp')))
        self.assertTrue(os.path.isfile(os.path.join(self.d, 'photos', 'journeys-lg', 'osprey.webp'))); self.assertEqual(w.pics['osprey']['wiki'], 'Osprey')

    def test_the_picture_and_its_larger_copy_land_in_the_same_commit(self):
        self.run_([strategy('wikipedia', found={'knot'})], only='wikipedia')
        w = self.fresh(); self.assertTrue(w.has('knot') and w.has_large('knot')); self.assertEqual(w.check(), [])
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos', 'species')))   # nothing outside the journey folders

    def test_a_flow_journey_is_offered_only_to_wikipedia_and_commons(self):
        offered = []
        self.run_([strategy(n, offered=offered) for n in ('wikipedia', 'commons', 'gbif', 'openverse', 'inaturalist')])
        for n in ('wikipedia', 'commons'): self.assertIn((n, 'dust'), offered)
        for n in ('gbif', 'openverse', 'inaturalist'): self.assertNotIn((n, 'dust'), offered); self.assertIn((n, 'knot'), offered)

    def test_a_flow_journey_whose_page_picture_is_a_map_is_skipped_and_the_log_says_which_file(self):
        ss.SKIPPED['Saharan Air Layer'] = 'Saharan_Air_Layer_map.png'
        try:
            def find(todo):
                for u in todo: yield u, ss.Res('miss', why='skipped as not a photo (map, diagram, logo or flag): %s' % ss.SKIPPED[u['title']], status='nophoto')
            self.run_([('wikipedia', find, lambda w, u: u['sid'] == 'dust', None)])
        finally: ss.SKIPPED.pop('Saharan Air Layer', None)
        self.assertTrue(any(l.startswith('no wikipedia dust') and 'skipped as not a photo' in l and 'Saharan_Air_Layer_map.png' in l for l in self.log), self.log)
        w = self.fresh(); self.assertFalse(w.has('dust')); self.assertEqual(w.miss_['dust']['status'], 'nophoto')

    def test_the_wikipedia_source_names_the_skipped_file_for_a_map_page_image(self):
        calls = []
        def fake_get(q, raw=False, tries=None):
            calls.append(q)
            return {'query': {'pages': {'1': {'title': 'Saharan Air Layer', 'thumbnail': {'source': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Saharan_Air_Layer_map.png/330px-Saharan_Air_Layer_map.png'}}}}}
        old = ss.wm.get; ss.wm.get = fake_get
        try: res = list(ss.find_wikipedia([dict(sid='dust', title='Saharan Air Layer', name='', latin='', abiotic=True)]))
        finally: ss.wm.get = old; ss.SKIPPED.clear()
        self.assertEqual(res[0][1].kind, 'miss'); self.assertEqual(res[0][1].status, 'nophoto'); self.assertIn('Saharan_Air_Layer_map.png', res[0][1].why)

    def test_a_cc_by_picture_with_no_author_is_refused_and_recorded(self):
        al.lookup = lambda fn: ('none', '')
        self.run_([strategy('wikipedia', found={'knot'}, entry=lambda sid: row(sid, a='Unknown author'))])
        w = self.fresh(); self.assertFalse(w.has('knot')); self.assertEqual(w.miss_['knot']['status'], 'notfree')
        self.assertTrue(any(l.startswith('refused wikipedia') and 'no author' in l for l in self.log))

    def test_a_held_journey_is_not_tried_again_unless_asked_and_a_migrated_notyet_row_is_tried(self):
        w = self.w; w.miss('knot', 'nophoto', 'wikipedia'); w.miss('dust', 'notyet', now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc) - __import__('datetime').timedelta(days=1)); w.commit(); self.w = self.fresh(); offered = []
        self.run_([strategy('wikipedia', offered=offered)])
        self.assertNotIn(('wikipedia', 'knot'), offered)   # a 180-day 'no photo' is held
        self.assertIn(('wikipedia', 'dust'), offered)      # the migration's 'notyet' row is held 2 hours only, so a day later the job tries it
        offered.clear(); self.w = self.fresh(); self.run_([strategy('wikipedia', offered=offered)], again=True); self.assertIn(('wikipedia', 'knot'), offered)

    def test_dry_writes_nothing_and_limit_counts_titles(self):
        self.run_([strategy('wikipedia', found={'knot', 'osprey', 'chesosprey', 'dust'})], dry=True)
        self.assertEqual(self.fresh().pics, {}); self.assertTrue(any(l.startswith('yes wikipedia') for l in self.log))
        self.log.clear(); self.run_([strategy('wikipedia', found={'knot', 'osprey', 'chesosprey', 'dust'})], limit=2)
        self.assertEqual(len(self.fresh().pics), 3)   # two titles in id order: Osprey (two journeys) and Saharan Air Layer

    def test_the_large_strategy_makes_only_the_missing_400_px_copies_and_never_a_192_px_one(self):
        self.run_([strategy('wikipedia', found={'knot'})], only='wikipedia', copies=lambda e, need=('large',): ({}, 'no thumbnail'))
        w = self.fresh(); self.assertTrue(w.has('knot')); self.assertFalse(w.has_large('knot'))
        self.w = self.fresh(); self.run_([], only='large'); self.assertFalse(self.fresh().has_large('knot'), 'the failed copy is held for 30 days (#1183)')
        self.w = self.fresh(); self.run_([], only='large', again=True); self.assertTrue(self.fresh().has_large('knot')); self.assertEqual(self.fresh().check(), [])

    def test_a_source_that_stops_is_reported(self):
        def boom(todo):
            raise RuntimeError('refused')
            yield
        stats, stopped = self.run_([('wikipedia', boom, lambda w, u: True, None)]); self.assertEqual(stopped, ['wikipedia']); self.assertTrue(any(l.startswith('STOP wikipedia') for l in self.log))


class MainTests(unittest.TestCase):
    def call(self, d, args):
        old = sys.stdout; sys.stdout = io.StringIO(); saved = jj.STRATEGIES; cwd = os.getcwd(); os.chdir(d)
        try: return jj.main(args, root=d), sys.stdout.getvalue()
        finally: sys.stdout = old; jj.STRATEGIES = saved; os.chdir(cwd)

    def test_refused_until_the_migration_has_run(self):
        d = tempfile.mkdtemp(); code, out = self.call(d, []); self.assertEqual(code, 1); self.assertIn('migration', out)

    def test_unknown_strategy_exits_1_and_a_stopped_source_exits_2(self):
        d = tree([('knot', 'species', 'Red knot')]); self.assertEqual(self.call(d, ['--strategy', 'nope'])[0], 1)
        def boom(todo):
            raise RuntimeError('refused')
            yield
        old = jj.STRATEGIES; jj.STRATEGIES = [('wikipedia', boom, lambda w, u: True, None)]
        try: code, out = self.call(d, ['--strategy', 'wikipedia'])
        finally: jj.STRATEGIES = old
        self.assertEqual(code, 2); self.assertIn('STOP wikipedia', out)

    def test_a_good_run_writes_through_the_journey_writer_and_checks_clean(self):
        d = tree([('knot', 'species', 'Red knot')])
        def find(todo):
            for u in todo: yield u, ss.Res('found', row(u['sid']), jpeg(), note='f.jpg')
        old_c = jj.copies; jj.copies = fake_copies; saved = jj.STRATEGIES; jj.STRATEGIES = [('wikipedia', find, lambda w, u: True, None)]
        old = sys.stdout; sys.stdout = io.StringIO()
        try: code = jj.main([], root=d)
        finally: sys.stdout = old; jj.copies = old_c; jj.STRATEGIES = saved
        w = jp.JourneyPhotos(d); self.assertEqual(code, 0); self.assertTrue(w.has('knot') and w.has_large('knot')); self.assertEqual(w.check(), [])


if __name__ == '__main__': unittest.main()
