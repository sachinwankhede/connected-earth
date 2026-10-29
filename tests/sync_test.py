"""Tests for pipeline/syncmain.py: every kind of clash the data jobs have produced, built as a small throwaway git repository.
Run: python3 -m unittest tests/sync_test.py   (or node --test tests/sync.test.mjs, which CI runs)"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); SCRIPT = os.path.join(os.path.dirname(HERE), 'pipeline', 'syncmain.py')

def git(cwd, *a, check=True):
    return subprocess.run(('git',) + a, cwd=cwd, capture_output=True, text=True, check=check)

class Repo:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix='synctest_')
        git(self.dir, 'init', '-q', '-b', 'main'); git(self.dir, 'config', 'user.email', 't@t'); git(self.dir, 'config', 'user.name', 't')
        for d in ('data', 'data-auto', 'pipeline'): os.makedirs(os.path.join(self.dir, d))
    def put(self, path, obj):
        p = os.path.join(self.dir, path); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))
    def get(self, path): return json.load(open(os.path.join(self.dir, path)))
    def exists(self, path): return os.path.exists(os.path.join(self.dir, path))
    def commit(self, msg): git(self.dir, 'add', '-A'); git(self.dir, 'commit', '-q', '-m', msg)
    def branch(self, name): git(self.dir, 'checkout', '-q', '-b', name)
    def checkout(self, name): git(self.dir, 'checkout', '-q', name)
    def merge_main(self, *opts): return git(self.dir, 'merge', '--no-edit', *opts, 'main', check=False)
    def sync(self):
        return subprocess.run([sys.executable, SCRIPT], cwd=self.dir, env=dict(os.environ, SYNC_ROOT=self.dir), capture_output=True, text=True)
    def cleanup(self): shutil.rmtree(self.dir, ignore_errors=True)

def place(**kw):
    e = {'id': 'p', 'name': 'P', 'story': None, 'nodes': [{'id': 'a', 'sp': 'x', 'xh': 1}], 'raw': [['a', 'b']], 'ev': {'a>b': ['g', 'x', 'y']}, 'tip': {'id': 'a'}}
    e.update(kw); return e

class SyncTests(unittest.TestCase):
    def setUp(self): self.r = Repo(); self.addCleanup(self.r.cleanup)

    def start(self, files):
        for p, o in files.items(): self.r.put(p, o)
        self.r.commit('base'); self.r.branch('feature'); self.r.checkout('main')

    def promote(self):
        # main moves the place to data/ and rewrites it (packing, story, photo...), so git cannot pair the two files as a rename and reports modify/delete
        os.remove(os.path.join(self.r.dir, 'data-auto/p.json'))
        self.r.put('data/p.json', {'id': 'p', 'name': 'Promoted', 'story': 'S', 'imgwiki': 'I', 'level': 'local', 'sources': [{'t': 'x'}] * 5, 'nodes': [{'id': 'zz', 'sp': 'q', 'xh': 9}] * 6, 'raw': [], 'ev': {}})
        self.r.commit('promote')

    def test_repack_on_branch_new_story_on_main(self):
        self.start({'data/p.json': place()})
        self.r.checkout('feature'); self.r.put('data/p.json', place(nodes=[{'id': 'a', 'sp': 'x', 'xh': 1, 'no': ['tl']}])); self.r.commit('repack')
        self.r.checkout('main'); self.r.put('data/p.json', place(story='A story.')); self.r.commit('story')
        self.r.checkout('feature'); self.assertNotEqual(self.r.merge_main().returncode, 0)
        out = self.r.sync(); self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        e = self.r.get('data/p.json'); self.assertEqual(e['story'], 'A story.'); self.assertEqual(e['nodes'], place()['nodes'])   # main's story and main's web

    def test_branch_rebuilt_web_is_kept_while_main_changes_the_rest(self):
        self.start({'data-auto/p.json': place()})
        new = {'raw': [['a', 'c']], 'ev': {'a>c': ['gg', 'x', 'z']}, 'nodes': [{'id': 'a', 'sp': 'x', 'xh': 1}, {'id': 'c', 'sp': 'z', 'xh': 2}], 'tip': {'id': 'c'}}
        self.r.checkout('feature'); self.r.put('data-auto/p.json', place(**new)); self.r.commit('regen')
        self.r.checkout('main'); self.r.put('data-auto/p.json', place(imgwiki='Photo', nodes=[{'id': 'a', 'sp': 'x', 'xh': 1, 'no': ['tl']}])); self.r.commit('photo and repack')
        self.r.checkout('feature'); self.assertNotEqual(self.r.merge_main().returncode, 0)
        out = self.r.sync(); self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        e = self.r.get('data-auto/p.json')
        self.assertEqual(e['raw'], new['raw']); self.assertEqual(e['tip'], new['tip']); self.assertEqual(e['imgwiki'], 'Photo')

    def test_promotion_on_main_stands_when_branch_only_repacked(self):
        self.start({'data-auto/p.json': place()})
        self.r.checkout('feature'); self.r.put('data-auto/p.json', place(nodes=[{'id': 'a', 'sp': 'x', 'xh': 1, 'no': ['tl']}])); self.r.commit('repack')
        self.r.checkout('main'); self.promote()
        self.r.checkout('feature'); self.assertNotEqual(self.r.merge_main().returncode, 0)
        out = self.r.sync(); self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertFalse(self.r.exists('data-auto/p.json')); self.assertTrue(self.r.exists('data/p.json'))

    def test_promotion_on_main_stops_when_branch_rebuilt_the_place(self):
        self.start({'data-auto/p.json': place()})
        self.r.checkout('feature'); self.r.put('data-auto/p.json', place(raw=[['a', 'c']])); self.r.commit('regen')
        self.r.checkout('main'); self.promote()
        self.r.checkout('feature'); self.r.merge_main()
        out = self.r.sync(); self.assertEqual(out.returncode, 1); self.assertIn('need a person', out.stdout)

    def test_names_and_species_and_order_are_unioned(self):
        self.start({'pipeline/names.json': {'a': None, 'b': 'B'}, 'data/species.json': {'x': {'name': 'X'}}, 'data-auto/order.json': ['o1']})
        self.r.checkout('feature')
        self.r.put('pipeline/names.json', {'a': None, 'b': 'B', 'c': 'C'}); self.r.put('data/species.json', {'x': {'name': 'X'}, 'f': {'name': 'F'}})
        self.r.put('data-auto/order.json', ['o1', 'of']); self.r.put('data-auto/of.json', place(id='of')); self.r.commit('feature')
        self.r.checkout('main')
        self.r.put('pipeline/names.json', {'a': 'A', 'b': 'B', 'd': 'D'}); self.r.put('data/species.json', {'x': {'name': 'X'}, 'm': {'name': 'M'}})
        self.r.put('data-auto/order.json', ['o1', 'om']); self.r.put('data-auto/om.json', place(id='om')); self.r.commit('main')
        self.r.checkout('feature'); self.assertNotEqual(self.r.merge_main().returncode, 0)
        out = self.r.sync(); self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(self.r.get('pipeline/names.json'), {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'})
        self.assertEqual(set(self.r.get('data/species.json')), {'x', 'f', 'm'})
        self.assertEqual(self.r.get('data-auto/order.json'), ['o1', 'om', 'of'])

    def test_other_files_always_need_a_person(self):
        self.start({'docs/notes.md': 'base\n'})
        self.r.checkout('feature'); self.r.put('docs/notes.md', 'feature\n'); self.r.commit('f')
        self.r.checkout('main'); self.r.put('docs/notes.md', 'main\n'); self.r.commit('m')
        self.r.checkout('feature'); self.r.merge_main()
        out = self.r.sync(); self.assertEqual(out.returncode, 1); self.assertIn('docs/notes.md', out.stdout)

if __name__ == '__main__': unittest.main()
