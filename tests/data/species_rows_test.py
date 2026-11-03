"""One file per species (#276 step 2): the folder reads back as the old table, pack never rewrites an existing row, and only a missing species gets a new row."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build'))
import species

def row(latin, sid, **kw):
    return {'latin': latin, 'name': latin.upper(), 'tl': 2, 'wiki': latin, 'desc': 'd', 'ic': 'x', 'sid': sid, 'sk': 'taxon', **kw}

class Rows(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.root = self.d.name
        self.rows = os.path.join(self.root, 'data', 'species', 'rows'); os.makedirs(self.rows)
    def tearDown(self): self.d.cleanup()
    def test_row_path_uses_first_two_letters_of_sid(self):
        self.assertEqual(species.row_path('abies-balsamea', '/r'), '/r/ab/abies-balsamea.json')
    def test_table_reads_the_folder_like_the_old_file(self):
        a, b = row('Abies x', 'abies-x'), row('Zea y', 'zea-y', about='A.')
        for r in (b, a): species.write_row(r, self.rows)
        self.assertEqual(species.table(self.root), {'abies x': a, 'zea y': b})
        self.assertEqual(list(species.table(self.root)), ['abies x', 'zea y'])   # sorted like the old file
    def test_table_falls_back_to_the_old_file(self):
        os.makedirs(os.path.join(self.root, 'x')); r2 = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(r2.name, 'data', 'species')); json.dump({'a b': row('A b', 'a-b')}, open(os.path.join(r2.name, 'data', 'species', 'species.json'), 'w'))
        self.assertEqual(list(species.table(r2.name)), ['a b']); r2.cleanup()
    def test_provenance_fields_do_not_reach_the_built_nodes(self):
        tab = {'a b': row('A b', 'a-b', src='legacy', at='2026-11-03')}
        node = species.join({'id': 'p', 'nodes': [{'id': 'n', 'sp': 'a b', 'xh': 1}]}, tab)['nodes'][0]
        self.assertNotIn('src', node); self.assertNotIn('at', node); self.assertNotIn('sid', node)

class PackAndSplit(unittest.TestCase):
    """pack() and split() on a throwaway tree (the module's paths are pointed at it)."""
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); r = self.d.name
        self.keep = (species.ROOT, species.TABLE, species.ROWS, species.files)
        species.ROOT = r; species.TABLE = os.path.join(r, 'data', 'species', 'species.json'); species.ROWS = os.path.join(r, 'data', 'species', 'rows')
        os.makedirs(os.path.join(r, 'data', 'species')); os.makedirs(os.path.join(r, 'data', 'places'))
        self.place = os.path.join(r, 'data', 'places', 'p.json')
        species.files = lambda: iter([self.place])
        self.stdout = sys.stdout; sys.stdout = open(os.devnull, 'w')
    def tearDown(self):
        sys.stdout = self.stdout; species.ROOT, species.TABLE, species.ROWS, species.files = self.keep; self.d.cleanup()
    def node(self, i, latin, name):
        return {'id': i, 'latin': latin, 'name': name, 'tl': 2, 'xh': 1, 'wiki': latin, 'desc': 'd', 'ic': 'x'}
    def test_split_then_table_is_the_old_table(self):
        old = {'a b': row('A b', 'a-b'), 'c d': row('C d', 'c-d', about='x')}
        json.dump(old, open(species.TABLE, 'w')); species.split()
        self.assertFalse(os.path.exists(species.TABLE))
        self.assertEqual(species.table(), {k: {**v, 'src': 'legacy'} for k, v in old.items()})
    def test_pack_leaves_an_existing_row_alone_and_adds_a_new_one(self):
        species.write_row(row('A b', 'a-b', name='Old name', src='legacy'))
        json.dump({'id': 'p', 'nodes': [self.node('n1', 'A b', 'Changed by a vote'), self.node('n2', 'E f', 'New one')]}, open(self.place, 'w'))
        os.environ['SPECIES_SRC'] = 'test-job'
        try: species.pack()
        finally: del os.environ['SPECIES_SRC']
        tab = species.table()
        self.assertEqual(tab['a b']['name'], 'Old name')                       # never re-voted
        self.assertEqual(tab['e f']['name'], 'New one'); self.assertEqual(tab['e f']['src'], 'test-job'); self.assertRegex(tab['e f']['at'], r'^\d{4}-\d\d-\d\d$')
        slim = json.load(open(self.place))['nodes']
        self.assertEqual(slim[0]['name'], 'Changed by a vote')                  # the place keeps what differs from the row
        before = json.dumps(tab, sort_keys=True); species.pack()
        self.assertEqual(json.dumps(species.table(), sort_keys=True), before)  # safe to repeat

if __name__ == '__main__': unittest.main()
