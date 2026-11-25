#!/usr/bin/env python3
"""jobs/nodepictures.py: the node strategy of the acquire job (#1183). Fake sources only: no network. Everything runs in a temp root."""
import datetime, io, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import nodepictures as nj, speciespictures as sj, node_photos as np, species_sources as ss

def jpeg(color=(200, 180, 40), size=(300, 200)):
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', size, color).save(b, 'JPEG'); return b.getvalue()

def put(d, rel, obj):
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

def tree():
    """A root with two places that share the node Sunlight (title 'Sunbeam') and have Soil and a species node (not a unit)."""
    d = tempfile.mkdtemp()
    for pid in ('aa', 'bb'):
        nodes = [{'id': 'sun', 'name': 'Sunlight', 'cat': 'abiotic', 'wiki': 'Sunbeam'}, {'id': 'owl', 'name': 'Owl', 'latin': 'Strix varia', 'wiki': 'Barred owl'}]
        if pid == 'bb': nodes.append({'id': 'soil', 'name': 'Soil', 'cat': 'abiotic', 'wiki': 'Soil'})
        put(d, 'data/places/%s.json' % pid, {'id': pid, 'nodes': nodes, 'raw': [], 'ev': {}})
    return d

def row(nid, a='Jane Doe', l='CC BY 4.0'):
    return dict(a=a, l=l, lu='https://creativecommons.org/licenses/by/4.0/', p='https://commons.wikimedia.org/wiki/File:Some_file.jpg', page='Some', u='a/ab/Some_file.jpg/330px-Some_file.jpg')

def strategy(name, found=(), offered=None):
    def find(todo):
        for u in todo:
            if offered is not None: offered.append((name, u['sid']))
            if u['sid'] in found: yield u, ss.Res('found', row(u['sid']), jpeg(), note='file.jpg')
            else: yield u, ss.Res('miss', why='nothing', status='nophoto')
    rule = [s for s in nj.STRATEGIES if s[0] == name][0]
    return (name, find, rule[2], rule[3])

def fake_copies(entry, need=('medium',)): return ({'medium': b'MEDIUM-192'} if 'medium' in need else {}), ''
def no_copies(entry, need=('medium',)): return {}, 'no larger source'


class NodeAcquireTests(unittest.TestCase):
    def setUp(self):
        self.d = tree(); self.units = nj.load_units(self.d); self.w = nj.Photos(self.d); self.log = []
    def run_(self, strategies, copies=fake_copies, **kw): return sj.acquire(self.w, self.units, strategies, log=self.log.append, copies=copies, **kw)
    def fresh(self): return nj.Photos(self.d)

    def test_units_are_the_concepts_by_node_id_once_each_and_all_abiotic(self):
        self.assertEqual([(u['sid'], u['title'], u['abiotic']) for u in self.units], [('soil', 'Soil', True), ('sunbeam', 'Sunbeam', True)])

    def test_only_wikipedia_and_commons_are_offered_a_node(self):
        offered = []
        self.run_([strategy(n, offered=offered) for n in ('wikipedia', 'commons', 'gbif', 'openverse', 'inaturalist')])
        self.assertEqual(sorted({o[0] for o in offered}), ['commons', 'wikipedia'])

    def test_the_first_fetch_is_the_192_px_stored_file_and_nothing_else_is_written(self):
        self.run_([strategy('wikipedia', found={'sunbeam'})], copies=None)
        w = self.fresh(); self.assertTrue(w.has('sunbeam')); self.assertEqual(w.check(), [])
        files = os.listdir(os.path.join(self.d, 'photos', 'nodes')); self.assertEqual(files, [w.pics['sunbeam']['f']])
        from PIL import Image
        self.assertEqual(Image.open(os.path.join(self.d, 'photos', 'nodes', files[0])).size, (192, 128))
        self.assertEqual(sorted(os.listdir(os.path.join(self.d, 'photos'))), ['node_missing.json', 'node_pictures.json', 'node_tried.json', 'nodes'])
        self.assertEqual(w.pics['sunbeam']['wiki'], 'Sunbeam')

    def test_a_wikipedia_miss_is_recorded_and_commons_then_holds_it_for_30_days(self):
        self.run_([strategy('wikipedia'), strategy('commons')])
        w = self.fresh(); self.assertEqual(sorted(w.miss_), ['soil', 'sunbeam']); self.assertEqual(w.miss_['soil']['status'], 'nophoto')
        today = datetime.date.today(); self.assertTrue(sj.held(w, 'soil', 'commons', 30, today))
        self.assertFalse(sj.held(w, 'soil', 'commons', 30, today + datetime.timedelta(days=31)))
        offered = []; self.w = w; self.run_([strategy('commons', offered=offered)]); self.assertEqual(offered, [])

    def test_a_node_missing_long_ago_is_tried_again_and_leaves_missing_when_found(self):
        self.w.miss('soil', 'nophoto', 'wikipedia', now=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)); self.w.commit(); self.w = self.fresh()
        self.run_([strategy('commons', found={'soil'})])
        w = self.fresh(); self.assertTrue(w.has('soil')); self.assertNotIn('soil', w.miss_); self.assertEqual(w.check(), [])

    def test_a_licence_that_needs_an_author_is_refused_and_nothing_is_stored(self):
        def find(todo):
            for u in todo: yield u, ss.Res('found', dict(row(u['sid']), a='Unknown author'), jpeg(), note='f.jpg')
        import author_lookup as al; old = al.lookup; al.lookup = lambda fn: ('none', '')
        try: stats, _ = self.run_([('wikipedia', find, lambda w, u: True, None)])
        finally: al.lookup = old
        self.assertEqual(stats['wikipedia']['found'], 0); self.assertGreater(stats['wikipedia']['refused'], 0); self.assertEqual(self.fresh().pics, {})

    def test_dry_writes_nothing(self):
        self.run_([strategy('wikipedia', found={'sunbeam'})], dry=True)
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos')))

    def test_main_runs_end_to_end_with_the_check_and_exit_codes(self):
        saved = nj.STRATEGIES; old = sys.stdout
        nj.STRATEGIES = [strategy('wikipedia', found={'sunbeam'}), strategy('commons')]; sys.stdout = io.StringIO()
        try: code = nj.main(['--strategy', 'wikipedia', '--repair-limit', '0'], root=self.d); bad = nj.main(['--strategy', 'nope'], root=self.d)
        finally: sys.stdout = old; nj.STRATEGIES = saved
        self.assertEqual((code, bad), (0, 1)); self.assertTrue(np.NodePhotos(self.d).has('sunbeam'))


if __name__ == '__main__': unittest.main()
