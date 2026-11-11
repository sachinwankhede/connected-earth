import os, sys, json, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import diets_resolve as D

def w(root, parts, data):
    p = os.path.join(root, *parts); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
NODES = [{'id': 'deer', 'sp': 'odocoileus virginianus'}, {'id': 'vul', 'sp': 'cathartes aura'}, {'id': 'coy', 'sp': 'canis latrans'}]
def place(kinds):   # kinds: {(from, to): 'e' or 's'}
    return {'id': 'p', 'nodes': NODES, 'raw': [[a, b] if k == 'e' else [a, b, 's'] for (a, b), k in kinds.items()] + [['sun', 'deer', 'r']], 'ev': {'deer>vul': ['g']}}
class Resolve(unittest.TestCase):
    def setUp(self):
        self.r = tempfile.mkdtemp()
        w(self.r, ['data', 'species', 'species.json'], {'odocoileus virginianus': {'sid': 'deer'}, 'cathartes aura': {'sid': 'vul'}, 'canis latrans': {'sid': 'coy'}})
        w(self.r, ['data', 'diets', 'vu', 'vul.json'], {'sid': 'vul', 'prey': {'deer': {'ev': ['g'], 'k': 'e'}}})
        # vulture and deer: scavenged in 9 places, eaten in 1 (a clear majority); coyote and deer: 5 and 5 (a tie)
        for i in range(10): w(self.r, ['data', 'places', 'p%d.json' % i], place({('deer', 'vul'): 'e' if i == 0 else 's', ('deer', 'coy'): 'e' if i < 5 else 's'}))
    def raw(self, i): return json.load(open(os.path.join(self.r, 'data', 'places', 'p%d.json' % i)))
    def test_dry_changes_nothing(self):
        fixed, left = D.resolve(self.r, dry=True); self.assertEqual(fixed, [('deer', 'vul', 's', 1)]); self.assertEqual([(a, b) for a, b, _ in left], [('deer', 'coy')])
        self.assertEqual(self.raw(0)['raw'][0], ['deer', 'vul'])
    def test_majority_wins_and_the_rest_is_kept(self):
        D.resolve(self.r); d = self.raw(0)
        self.assertEqual(d['raw'][0], ['deer', 'vul', 's']); self.assertEqual(d['raw'][1], ['deer', 'coy']); self.assertEqual(d['raw'][2], ['sun', 'deer', 'r'], 'rows that are not eating links stay')
        self.assertEqual(d['ev'], {'deer>vul': ['g']}, 'evidence is not touched'); self.assertEqual(self.raw(1)['raw'][0], ['deer', 'vul', 's'])
    def test_a_tie_or_a_weak_majority_is_left_alone(self):
        D.resolve(self.r); self.assertEqual([r for r in self.raw(0)['raw'] if r[:2] == ['deer', 'coy']], [['deer', 'coy']]); self.assertEqual(self.raw(9)['raw'][1], ['deer', 'coy', 's'])

    def test_weak_majority(self):
        fixed, left = D.resolve(self.r, 0.95, dry=True); self.assertEqual(fixed, [], 'a 90% pair is not fixed at 95%'); self.assertEqual(sorted((x, y) for x, y, _ in left), [('deer', 'coy'), ('deer', 'vul')])
    def test_table_kind_follows(self):
        w(self.r, ['data', 'diets', 'vu', 'vul.json'], {'sid': 'vul', 'prey': {'deer': {'ev': ['g'], 'k': 'e'}}}); D.resolve(self.r)
        self.assertEqual(json.load(open(os.path.join(self.r, 'data', 'diets', 'vu', 'vul.json')))['prey']['deer']['k'], 's')
    def test_second_run_changes_nothing(self):
        D.resolve(self.r); fixed, left = D.resolve(self.r); self.assertEqual(fixed, [])
if __name__ == '__main__': unittest.main()
