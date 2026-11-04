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
                            (dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Acer', scientificName='Acer L.'), 'Quercus rubra'),   # a different name
                            (dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Acer', confidence=70), 'Acer')):
            ok, _ = taxonomy.classify({'tl': 3, 'latin': latin}, resp)
            self.assertFalse(ok, latin)
    def test_producer_matching_an_animal_goes_to_review(self):
        ok, rec = taxonomy.classify({'tl': 1, 'latin': 'Liana'}, dict(EXACT, matchType='EXACT'))   # EXACT is Animalia in this fixture
        self.assertFalse(ok); self.assertIn('producer matched an animal', rec['why'])
    def test_subspecies_falls_back_to_the_parent(self):
        resp = dict(EXACT, matchType='HIGHERRANK', rank='SPECIES', canonicalName='Cervus canadensis', scientificName='Cervus canadensis Erxleben, 1777', confidence=95)
        ok, rec = taxonomy.classify({'tl': 2, 'latin': 'Cervus canadensis roosevelti'}, resp)
        self.assertTrue(ok); self.assertEqual((rec['match'], rec['rank']), ('higher-rank', 'SPECIES'))
        ok, rec = taxonomy.classify({'tl': 1, 'latin': 'Opuntia species'}, dict(EXACT, matchType='HIGHERRANK', rank='GENUS', canonicalName='Opuntia', kingdom='Plantae', confidence=95))
        self.assertTrue(ok)
        ok, _ = taxonomy.classify({'tl': 2, 'latin': 'Cervus other'}, dict(resp, canonicalName='Cervus canadensis'))   # not the start of our name
        self.assertFalse(ok)
    def test_spelling_variants(self):
        fz = dict(EXACT, matchType='FUZZY', canonicalName='Gyps rueppellii', scientificName='Gyps rueppellii (A.E.Brehm, 1852)', confidence=98)
        ok, rec = taxonomy.classify({'tl': 3, 'latin': 'Gyps rueppelli'}, fz)
        self.assertTrue(ok); self.assertEqual(rec['match'], 'fuzzy')
        for row, resp in (({'tl': 3, 'latin': 'Gyps rueppelli'}, dict(fz, confidence=90)),          # not sure enough
                          ({'tl': 2, 'latin': 'Porcella salvania'}, dict(fz, canonicalName='Porcula salvania')),   # different genus
                          ({'tl': 3, 'latin': 'Gyps rueppelli'}, dict(fz, canonicalName='Gyps fulvus'))):          # too far apart
            self.assertFalse(taxonomy.classify(row, resp)[0], row)
    def test_edits(self):
        self.assertEqual((taxonomy.edits('a', 'a'), taxonomy.edits('rueppelli', 'rueppellii'), taxonomy.edits('abc', 'xyz')), (0, 1, 3))
    def test_name_in_several_kingdoms_is_asked_again(self):
        calls = []
        def fake(name, kingdom=None):
            calls.append(kingdom)
            if kingdom is None: return {'matchType': 'NONE', 'note': 'Multiple equal matches for Ficus'}
            if kingdom == 'Plantae': return dict(EXACT, matchType='EXACT', kingdom='Plantae', rank='GENUS', canonicalName='Ficus')
            return {'matchType': 'NONE'}
        old = taxonomy.gbif; taxonomy.gbif = fake
        try: r = taxonomy.lookup({'tl': 1, 'latin': 'Ficus'})
        finally: taxonomy.gbif = old
        self.assertEqual((r['kingdom'], calls), ('Plantae', [None, 'Plantae']))
        taxonomy.gbif = lambda n, k=None: {'matchType': 'HIGHERRANK', 'rank': 'KINGDOM', 'canonicalName': k or 'x'} if k else {'matchType': 'NONE', 'note': 'Multiple equal matches for Ulva'}
        try: r = taxonomy.lookup({'tl': 1, 'latin': 'Ulva'})
        finally: taxonomy.gbif = old
        self.assertEqual(r['matchType'], 'NONE')   # only kingdom-level answers: stays unmatched
    def test_name_search_pick(self):
        fish = {'canonicalName': 'Acanthurus', 'taxonomicStatus': 'ACCEPTED', 'rank': 'GENUS', 'kingdom': 'Animalia', 'phylum': 'Chordata', 'order': 'Perciformes', 'family': 'Acanthuridae', 'key': 2379647, 'scientificName': 'Acanthurus Forsskal, 1775'}
        beetle = dict(fish, taxonomicStatus='DOUBTFUL', phylum='Arthropoda', family='Curculionidae', key=1217425)
        ok, rec = taxonomy.pick({'tl': 2, 'latin': 'Acanthurus'}, [beetle, fish], at='2026-11-04')
        self.assertTrue(ok); self.assertEqual((rec['family'], rec['match'], rec['key'], 'conf' in rec), ('Acanthuridae', 'name-search', 2379647, False))
        # a producer never takes the animal; a consumer never takes the plant
        plant = dict(fish, canonicalName='Ulva', kingdom='Plantae', family='Ulvaceae'); insect = dict(plant, kingdom='Animalia', family='Hesperiidae', key=1)
        self.assertEqual(taxonomy.pick({'tl': 1, 'latin': 'Ulva'}, [insect, plant])[1]['family'], 'Ulvaceae')
        self.assertFalse(taxonomy.pick({'tl': 2, 'latin': 'Ulva'}, [plant])[0])
        # two accepted taxa with the name, a different name, or nothing: no guess
        self.assertFalse(taxonomy.pick({'tl': 2, 'latin': 'Acanthurus'}, [fish, dict(fish, key=2)])[0])
        self.assertFalse(taxonomy.pick({'tl': 2, 'latin': 'Scarus'}, [fish])[0])
        self.assertFalse(taxonomy.pick({'tl': 2, 'latin': 'Acanthurus'}, [])[0])
        self.assertFalse(taxonomy.pick({'tl': 2, 'latin': 'Acanthurus'}, [dict(fish, rank='KINGDOM')])[0])
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
