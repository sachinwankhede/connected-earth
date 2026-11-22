import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import species_report as r, collections

def row(sid, name, sk='resource'): return {'sid': sid, 'name': name, 'sk': sk}

class Groups(unittest.TestCase):
    def test_same_name_rows_are_one_group_with_their_node_counts(self):
        g = r.groups([row('a', 'Decomposers'), row('b', 'Decomposers'), row('c', 'Soil')], collections.Counter({'a': 3, 'b': 1}))
        self.assertEqual(g, [('same-name', 'resource', 'Decomposers', [('a', 'Decomposers', 3), ('b', 'Decomposers', 1)])])
    def test_wording_variants_group_but_different_kinds_do_not(self):
        g = r.groups([row('a', 'Forest soil & litter'), row('b', 'Forest soils and litter'), row('c', 'Forest soil and litter', 'taxon')], collections.Counter())
        self.assertEqual([(c, k, [s for s, _, _ in m]) for c, k, _, m in g], [('wording', 'resource', ['a', 'b'])])
    def test_a_different_concept_is_not_grouped(self):
        self.assertEqual(r.groups([row('a', 'Forest soil'), row('b', 'Peat soil')], collections.Counter()), [])

if __name__ == '__main__': unittest.main()
