import os, sys, json, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import taxonomy
from validate_data import check

EXACT = {'matchType': 'EXACT', 'confidence': 98, 'scientificName': 'Ursus arctos Linnaeus, 1758', 'rank': 'SPECIES', 'usageKey': 2433433,
         'kingdom': 'Animalia', 'phylum': 'Chordata', 'class': 'Mammalia', 'order': 'Carnivora', 'family': 'Ursidae'}

class Classify(unittest.TestCase):
    def test_exact_is_accepted(self):
        ok, rec = taxonomy.classify({'tl': 3}, EXACT, at='2026-11-04')
        self.assertTrue(ok)
        self.assertEqual((rec['kingdom'], rec['class'], rec['family'], rec['key'], rec['src'], rec['match']), ('Animalia', 'Mammalia', 'Ursidae', 2433433, 'gbif', 'exact'))
    def test_higher_rank_keeps_only_ranks_it_has(self):
        r = dict(EXACT, rank='FAMILY'); del r['order']
        ok, rec = taxonomy.classify({'tl': 3}, r)
        self.assertTrue(ok); self.assertNotIn('order', rec); self.assertEqual(rec['rank'], 'FAMILY')
    def test_not_accepted(self):
        for resp, why in ((dict(EXACT, matchType='FUZZY'), 'fuzzy'), (dict(EXACT, matchType='HIGHERRANK'), 'higher-rank'), ({'matchType': 'NONE'}, 'no exact'),
                          (dict(EXACT, confidence=80), 'below 90'), (dict(EXACT, kingdom='Plantae'), 'expected Animalia'), (dict(EXACT, kingdom=''), 'no kingdom')):
            ok, rec = taxonomy.classify({'tl': 3}, resp)
            self.assertFalse(ok, why); self.assertIn(why, rec['why'])
    def test_same_name_higher_rank_is_accepted(self):
        genus = dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Acer', scientificName='Acer L.', confidence=92)
        ok, rec = taxonomy.classify({'tl': 1, 'latin': 'Acer'}, dict(genus, kingdom='Plantae'))
        self.assertTrue(ok); self.assertEqual((rec['match'], rec['rank']), ('higher-rank', 'GENUS'))
    def test_other_higher_rank_stays_in_review(self):
        for resp, latin in ((dict(EXACT, matchType='HIGHERRANK', rank='KINGDOM', canonicalName='Animalia', scientificName='Animalia'), 'Acanthurus'),
                            (dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Acer', scientificName='Acer L.'), 'Acer rubrum'),
                            (dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Acer', confidence=70), 'Acer')):
            ok, _ = taxonomy.classify({'tl': 3, 'latin': latin}, resp)
            self.assertFalse(ok, latin)
    def test_producer_matching_an_animal_goes_to_review(self):
        ok, rec = taxonomy.classify({'tl': 1, 'latin': 'Liana'}, dict(EXACT, matchType='EXACT'))   # EXACT is Animalia in this fixture
        self.assertFalse(ok); self.assertIn('producer matched an animal', rec['why'])
    def test_producer_has_no_kingdom_hint(self):
        self.assertIsNone(taxonomy.hint({'tl': 1})); self.assertEqual(taxonomy.hint({'tl': 2}), 'Animalia')
        ok, _ = taxonomy.classify({'tl': 1}, dict(EXACT, kingdom='Plantae'))
        self.assertTrue(ok)

def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

class Validator(unittest.TestCase):
    def tree(self, r):
        put(r, 'data/places/p.json', {}); put(r, 'data/order/0000-main.json', ['p'])
        for sid, latin, sk in (('ab', 'Ab', 'taxon'), ('cd', 'Cd', 'taxon'), ('ef', 'Ef', 'group')):
            put(r, 'data/species/rows/%s/%s.json' % (sid, sid), {'latin': latin, 'name': latin, 'tl': 2, 'wiki': latin, 'desc': 'd', 'ic': 'x', 'sid': sid, 'sk': sk})
    def test_clean(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            ok, rec = taxonomy.classify({'tl': 2}, EXACT, at='2026-11-04')
            put(r, 'data/species/taxonomy.json', {'ab': rec})
            put(r, 'data/species/taxonomy_review.json', {'cd': taxonomy.classify({'tl': 2}, {'matchType': 'NONE'}, at='2026-11-04')[1]})
            self.assertEqual(check(r)[0], [])
    def test_problems(self):
        with tempfile.TemporaryDirectory() as r:
            self.tree(r)
            ok, rec = taxonomy.classify({'tl': 2}, EXACT, at='2026-11-04')
            put(r, 'data/species/taxonomy.json', {'ab': rec, 'ef': rec, 'zz': dict(rec, extra=1)})
            put(r, 'data/species/taxonomy_review.json', {'ab': {'match': 'none', 'conf': 0, 'why': 'x', 'at': '2026-11-04'}})
            text = ' | '.join(check(r)[0])
            for want in ("'ef' is not a species of kind taxon", "'zz' is not a species of kind taxon", "Additional properties are not allowed ('extra'", "'ab' is both accepted and in the review list"):
                self.assertIn(want, text)

if __name__ == '__main__': unittest.main()
