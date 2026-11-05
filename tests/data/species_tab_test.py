#!/usr/bin/env python3
"""The Species tab files (#422): the groups, the top list, the pages. Made-up data for the rules; the built files for the real totals."""
import json, os, sys, unittest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

class SpeciesTab(unittest.TestCase):
    def test_groups_from_kingdom_and_class(self):
        g = B.species_group
        self.assertEqual(g({'kingdom': 'Animalia', 'class': 'Aves'}), 'birds'); self.assertEqual(g({'kingdom': 'Animalia', 'class': 'Mammalia'}), 'mammals')
        self.assertEqual(g({'kingdom': 'Animalia', 'class': 'Squamata'}), 'reptiles'); self.assertEqual(g({'kingdom': 'Animalia', 'class': 'Elasmobranchii'}), 'fish')
        self.assertEqual(g({'kingdom': 'Animalia', 'class': 'Insecta'}), 'insects'); self.assertEqual(g({'kingdom': 'Animalia'}), 'animals')
        self.assertEqual(g({'kingdom': 'Plantae', 'class': 'Pinopsida'}), 'plants'); self.assertEqual(g({'kingdom': 'Fungi'}), 'fungi')
        self.assertEqual(g({'kingdom': 'Chromista'}), 'other'); self.assertEqual(g(None), 'other')

    def test_rows_order_pages_and_totals(self):
        sp = {'A a': ['p1', 'p2', 'p3'], 'B b': ['p1'], 'C c': ['p1', 'p2'], 'D d': ['p1', 'p2']}
        common = {'A a': 'Alpha', 'B b': 'Beta', 'C c': 'Charlie', 'D d': 'Delta'}
        f = B.split_species_tab(sp, common, {'A a': 'birds', 'B b': 'birds', 'C c': 'plants', 'D d': 'plants'}, {'A a': 'x.webp'})
        self.assertEqual(f['top.json'], [['A a', 'Alpha', 3, 'x.webp'], ['C c', 'Charlie', 2, 0], ['D d', 'Delta', 2, 0], ['B b', 'Beta', 1, 0]], 'most places first, then by name; 0 when no picture')
        self.assertEqual(f['groups.json'], [['birds', 'Birds', 2, 1], ['plants', 'Plants', 2, 1]], 'only groups that have species')
        self.assertEqual(f['g-birds-0.json'], [['A a', 'Alpha', 3, 'x.webp'], ['B b', 'Beta', 1, 0]])
        big = {'S%d s' % i: ['p'] for i in range(B.TAB_PAGE * 2 + 1)}
        f = B.split_species_tab(big, {}, {l: 'plants' for l in big}, {})
        self.assertEqual(f['groups.json'], [['plants', 'Plants', len(big), 3]]); self.assertEqual(len(f['g-plants-2.json']), 1)
        self.assertEqual(len(f['top.json']), B.TAB_TOP)

    def test_built_files_add_up(self):
        for d in ('species-tab', 'species-tab-pilot'):
            p = os.path.join(ROOT, 'api', d)
            if not os.path.isdir(p): continue
            groups = json.load(open(os.path.join(p, 'groups.json'))); seen = set()
            for key, label, n, pages in groups:
                rows = [r for i in range(pages) for r in json.load(open(os.path.join(p, 'g-%s-%d.json' % (key, i))))]
                self.assertEqual(len(rows), n, key); seen |= {r[0] for r in rows}
                self.assertEqual(rows, sorted(rows, key=lambda r: (-r[2], r[1].lower(), r[0])), key + ' is in order')
            self.assertEqual(len(seen), sum(g[2] for g in groups), 'no species in two groups')
            top = json.load(open(os.path.join(p, 'top.json'))); self.assertEqual(len(top), B.TAB_TOP)
            self.assertTrue(all(r[0] in seen for r in top)); self.assertEqual([r[2] for r in top], sorted((r[2] for r in top), reverse=True))

if __name__ == '__main__':
    unittest.main()
