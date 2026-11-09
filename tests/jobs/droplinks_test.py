import os, sys, json, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import droplinks as D

def w(root, parts, data):
    p = os.path.join(root, *parts); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
class DropLinks(unittest.TestCase):
    def setUp(self):
        self.r = tempfile.mkdtemp()
        w(self.r, ['data', 'species', 'species.json'], {'pandion haliaetus': {'sid': 'pandion-haliaetus'}, 'odocoileus virginianus': {'sid': 'odocoileus-virginianus'}, 'alosa sapidissima': {'sid': 'alosa-sapidissima'}, 'aquila chrysaetos': {'sid': 'aquila-chrysaetos'}})
        w(self.r, ['data', 'species', 'taxonomy.json'], {'pandion-haliaetus': {'family': 'Pandionidae', 'class': 'Aves'}, 'odocoileus-virginianus': {'class': 'Mammalia', 'kingdom': 'Animalia'}, 'alosa-sapidissima': {'class': 'Actinopterygii'}, 'aquila-chrysaetos': {'family': 'Accipitridae', 'class': 'Aves'}})
        w(self.r, ['data', 'diets', 'pa', 'pandion-haliaetus.json'], {'sid': 'pandion-haliaetus', 'prey': {'odocoileus-virginianus': {'ev': ['g'], 'k': 'e'}, 'alosa-sapidissima': {'ev': ['g'], 'k': 'e'}}})
        w(self.r, ['data', 'diets', 'aq', 'aquila-chrysaetos.json'], {'sid': 'aquila-chrysaetos', 'prey': {'odocoileus-virginianus': {'ev': ['g'], 'k': 'e'}}})
        w(self.r, ['data', 'places', 'x.json'], {'id': 'x', 'nodes': [{'id': 'osp', 'sp': 'pandion haliaetus'}, {'id': 'deer', 'sp': 'odocoileus virginianus'}, {'id': 'shad', 'sp': 'alosa sapidissima'}, {'id': 'eag', 'sp': 'aquila chrysaetos'}],
            'raw': [['deer', 'osp'], ['shad', 'osp'], ['deer', 'eag']], 'ev': {'deer>osp': ['g'], 'shad>osp': ['g'], 'deer>eag': ['g']}})
    def test_rule(self):
        self.assertTrue(D.wrong({'family': 'Pandionidae'}, {'class': 'Mammalia'})); self.assertTrue(D.wrong({'family': 'Gaviidae'}, {'kingdom': 'Plantae'}))
        self.assertFalse(D.wrong({'family': 'Pandionidae'}, {'class': 'Actinopterygii'}), 'fish stay'); self.assertFalse(D.wrong({'family': 'Accipitridae'}, {'class': 'Mammalia'}), 'eagles stay')
        self.assertFalse(D.wrong({'family': 'Pandionidae'}, None), 'no taxonomy: not touched'); self.assertFalse(D.wrong(None, {'class': 'Mammalia'}))
    def test_dry_changes_nothing(self):
        pairs, rows, files = D.drop(self.r, True); self.assertEqual(pairs, [('odocoileus-virginianus', 'pandion-haliaetus')]); self.assertEqual((rows, files), (1, 1))
        self.assertEqual(len(json.load(open(os.path.join(self.r, 'data', 'places', 'x.json')))['raw']), 3)
    def test_drop(self):
        D.drop(self.r); d = json.load(open(os.path.join(self.r, 'data', 'places', 'x.json')))
        self.assertEqual(d['raw'], [['shad', 'osp'], ['deer', 'eag']]); self.assertEqual(sorted(d['ev']), ['deer>eag', 'shad>osp'])
        self.assertEqual(list(json.load(open(os.path.join(self.r, 'data', 'diets', 'pa', 'pandion-haliaetus.json')))['prey']), ['alosa-sapidissima'])
        self.assertEqual(list(json.load(open(os.path.join(self.r, 'data', 'diets', 'aq', 'aquila-chrysaetos.json')))['prey']), ['odocoileus-virginianus'])
    def test_consumer_left_with_nothing_loses_its_file(self):
        w(self.r, ['data', 'diets', 'pa', 'pandion-haliaetus.json'], {'sid': 'pandion-haliaetus', 'prey': {'odocoileus-virginianus': {'ev': ['g'], 'k': 'e'}}})
        D.drop(self.r); self.assertFalse(os.path.exists(os.path.join(self.r, 'data', 'diets', 'pa', 'pandion-haliaetus.json')))
if __name__ == '__main__': unittest.main()
