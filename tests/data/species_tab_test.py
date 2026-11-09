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

    def test_diet_rows_from_made_up_webs(self):   # #447: raw rows are [food, eater]
        ecos = [{'nodes': [{'id': 'g', 'latin': 'Grass g', 'name': 'Grass'}, {'id': 'd', 'latin': 'Deer d', 'name': 'Deer'}, {'id': 'w', 'latin': 'Wolf w', 'name': 'Wolf'}, {'id': 's', 'name': 'Sun', 'cat': 'sun'}],
                 'raw': [['g', 'd'], ['d', 'w'], ['s', 'g'], ['g', 'g']]},
                {'nodes': [{'id': 'd', 'latin': 'Deer d', 'name': 'Deer'}, {'id': 'w', 'latin': 'Wolf w', 'name': 'Wolf'}], 'raw': [['d', 'w']]}]
        about = {'deer-d': {'l': 'Deer d'}, 'wolf-w': {'l': 'Wolf w'}, 'grass-g': {'l': 'Grass g'}}
        B.species_diet(ecos, about, {'deer d': 'Deer', 'wolf w': 'Wolf', 'grass g': 'Grass'}, {'Deer d': 'd.webp'})
        self.assertEqual(about['wolf-w']['ea'], [['Deer d', 'Deer', 2, 'd.webp']]); self.assertNotIn('eb', about['wolf-w'])
        self.assertEqual(about['deer-d']['ea'], [['Grass g', 'Grass', 1, 0]]); self.assertEqual(about['deer-d']['eb'], [['Wolf w', 'Wolf', 2, 0]])
        self.assertNotIn('ea', about['grass-g'], 'the sun and itself are not food'); self.assertEqual(about['grass-g']['eb'], [['Deer d', 'Deer', 2, 'd.webp']])

    @unittest.skipUnless(os.path.exists(os.path.join(ROOT, 'api', 'species', 'pandion-haliaetus.json')), 'needs a build')
    def test_species_file_has_group_order_family(self):   # #446: the species page names them
        d = json.load(open(os.path.join(ROOT, 'api', 'species', 'pandion-haliaetus.json')))
        self.assertEqual((d.get('g'), d.get('od'), d.get('fa')), ('birds', 'Accipitriformes', 'Pandionidae'))
        groups = {g[0] for g in json.load(open(os.path.join(ROOT, 'api', 'species-tab', 'groups.json')))}
        self.assertIn(d['g'], groups, 'the group is one of the Species tab groups')

    @unittest.skipUnless(os.path.exists(os.path.join(ROOT, 'api', 'species', 'odocoileus-virginianus.json')) and os.path.exists(os.path.join(ROOT, 'photos', 'species_large.json')), 'needs a build')
    def test_species_file_marks_a_larger_picture(self):   # #421: pl = 1 only where photos/species-lg/ has a copy of the same picture
        large = json.load(open(os.path.join(ROOT, 'photos', 'species_large.json')))
        d = json.load(open(os.path.join(ROOT, 'api', 'species', 'odocoileus-virginianus.json')))
        self.assertEqual(d.get('pl'), 1 if d['ph'][0] in large.values() else None)

    def test_related_species_of_the_same_family(self):   # #448
        about = {'a': {'l': 'A a', 'fa': 'F1'}, 'b': {'l': 'B b', 'fa': 'F1'}, 'c': {'l': 'C c', 'fa': 'F1'}, 'd': {'l': 'D d', 'fa': 'F2'}, 'e': {'l': 'E e'}}
        B.species_related(about, {'a a': 'Alpha', 'b b': 'Beta', 'c c': 'Charlie'}, {'C c': 'c.webp'}, {'A a': 1, 'B b': 5, 'C c': 5})
        self.assertEqual(about['a']['rl'], [['B b', 'Beta', 5, 0], ['C c', 'Charlie', 5, 'c.webp']], 'most places first, then by name; not itself')
        self.assertEqual(about['b']['rl'][0][0], 'C c'); self.assertNotIn('rl', about['d'], 'alone in its family'); self.assertNotIn('rl', about['e'], 'no family')

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

    def test_orders_inside_a_group(self):   # #519 level 2
        sp = {'A a': ['p1', 'p2', 'p3'], 'B b': ['p1'], 'C c': ['p1', 'p2'], 'D d': ['p1'], 'E e': ['p1']}
        g = {l: 'birds' for l in sp}; g['E e'] = 'plants'
        f = B.split_species_tab(sp, {}, g, {}, {'A a': 'Strigiformes', 'B b': 'Passeriformes', 'C c': 'Passeriformes', 'D d': '', 'E e': 'Pinales'})
        self.assertEqual(f['groups.json'], [['birds', 'Birds', 4, 1, 3], ['plants', 'Plants', 1, 1]], 'a group with one order gets no order row')
        self.assertEqual(f['o-birds.json'], [['passeriformes', 'Passeriformes', 2, 1], ['other', 'Other', 1, 1], ['strigiformes', 'Strigiformes', 1, 1]], 'most species first, then by name')
        self.assertEqual([r[0] for r in f['g-birds-passeriformes-0.json']], ['C c', 'B b']); self.assertNotIn('o-plants.json', f)
        self.assertEqual(B.order_key('Carnivora'), 'carnivora'); self.assertEqual(B.order_key(None), 'other')
        self.assertNotIn('g-birds-pinales-0.json', f)
        self.assertEqual(B.split_species_tab(sp, {}, g, {})['groups.json'][0], ['birds', 'Birds', 4, 1], 'no orders given: as before')

    def test_built_files_add_up(self):
        for d in ('species-tab', 'species-tab-pilot'):
            p = os.path.join(ROOT, 'api', d)
            if not os.path.isdir(p): continue
            groups = json.load(open(os.path.join(p, 'groups.json'))); seen = set()
            for key, label, n, pages, *no in groups:
                rows = [r for i in range(pages) for r in json.load(open(os.path.join(p, 'g-%s-%d.json' % (key, i))))]
                self.assertEqual(len(rows), n, key); seen |= {r[0] for r in rows}
                self.assertEqual(rows, sorted(rows, key=lambda r: (-r[2], r[1].lower(), r[0])), key + ' is in order')
                if no:   # #519 level 2: the orders of a group hold each of its species once, in the same order
                    ol = json.load(open(os.path.join(p, 'o-%s.json' % key))); self.assertEqual(len(ol), no[0]); self.assertGreater(len(ol), 1)
                    orows = [r for k, name, c, pg in ol for i in range(pg) for r in json.load(open(os.path.join(p, 'g-%s-%s-%d.json' % (key, k, i))))]
                    self.assertEqual(sorted(r[0] for r in orows), sorted(r[0] for r in rows), key + ': every species is in exactly one order')
                    self.assertEqual([o[2] for o in ol], sorted((o[2] for o in ol), reverse=True), 'most species first')
            self.assertEqual(len(seen), sum(g[2] for g in groups), 'no species in two groups')
            top = json.load(open(os.path.join(p, 'top.json'))); self.assertEqual(len(top), B.TAB_TOP)
            self.assertTrue(all(r[0] in seen for r in top)); self.assertEqual([r[2] for r in top], sorted((r[2] for r in top), reverse=True))

if __name__ == '__main__':
    unittest.main()
