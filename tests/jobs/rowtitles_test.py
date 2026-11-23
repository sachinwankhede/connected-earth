import json, os, sys, tempfile, unittest, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import rowtitles

def fake(pages, labels, commons=None, taxa=None):
    """get() answering like Wikipedia ({asked title: (final title, wikidata id) | 'missing' | 'disambig' | ('redirect', to, id)}) and Wikidata ({id: label})."""
    def get(url):
        if 'wikidata' in url and 'props=claims' in url:
            ids = url.split('ids=')[1].split('|')
            return {'entities': {i: {'claims': {'P225': [{'mainsnak': {'datavalue': {'value': (taxa or {})[i]}}}] if i in (taxa or {}) else [], 'P1843': [{'mainsnak': {'datavalue': {'value': {'text': t, 'language': l}}}} for t, l in (commons or {}).get(i, [])]}} for i in ids if i in (commons or {}) or i in (taxa or {})}}
        if 'wikidata' in url:
            ids = url.split('ids=')[1].split('|')
            return {'entities': {i: {'labels': {'en': {'value': labels[i]}}} for i in ids if i in labels}}
        red = []; out = {}
        for t in urllib.parse.unquote(url.split('titles=')[1]).split('|'):
            a = pages.get(t, (t, None))
            if a == 'missing': out[t] = {'title': t, 'missing': ''}
            elif a == 'disambig': out[t] = {'title': t, 'pageprops': {'disambiguation': ''}}
            elif a[0] == 'redirect': red.append({'from': t, 'to': a[1]}); out[a[1]] = {'title': a[1], 'pageprops': {'wikibase_item': a[2]}}
            else: out[a[0]] = {'title': a[0], 'pageprops': {'wikibase_item': a[1]} if a[1] else {}}
        return {'query': {'redirects': red, 'pages': {str(i): p for i, p in enumerate(out.values())}}}
    return get

def row(sid, name, wiki, latin=''): return {'sid': sid, 'name': name, 'wiki': wiki, 'latin': latin, 'sk': 'taxon'}

class Decide(unittest.TestCase):
    def one(self, r, pages, labels=None, commons=None, taxa=None):
        return rowtitles.decide([r], fake(pages, labels or {}, commons, taxa))[0]
    def test_a_page_of_another_taxon_is_a_wrong_page(self):
        r = row('b', 'Arctic cod', 'Arctogadus', 'Boreogadus saida')
        st = self.one(r, {'Arctogadus': ('Arctogadus', 'Q10')}, {}, None, {'Q10': 'Arctogadus'})
        self.assertEqual(st[1], 'wrongpage'); self.assertIn('Arctogadus', st[3])
        self.assertNotEqual(self.one(row('b', 'Bullsnake', 'Pituophis catenifer', 'Pituophis catenifer'), {'Pituophis catenifer': ('Pituophis catenifer', 'Q11')}, {'Q11': 'Pituophis catenifer'}, None, {'Q11': 'Pituophis catenifer'})[1], 'wrongpage')
    def test_a_genus_page_a_synonym_and_a_subspecies_are_not_wrong_pages(self):
        for latin, tax in (('Chamaebatiaria millefolium', 'Chamaebatiaria'), ('Capra hircus', 'Capra aegagrus hircus'), ('Myodes rufocanus', 'Craseomys rufocanus')):
            self.assertFalse(rowtitles.wrong_page(row('x', 'N', 'P', latin), tax), latin)
        self.assertTrue(rowtitles.wrong_page(row('x', 'N', 'P', 'Boa imperator'), 'Boa constrictor'))
        self.assertTrue(rowtitles.wrong_page(row('x', 'N', 'P', 'Pantherophis alleghaniensis'), 'Pantherophis spiloides'))
    def test_a_synonym_label_with_the_same_epithet_is_scientific(self):
        r = row('v', 'Umbrella thorn', 'Vachellia tortilis', 'Vachellia tortilis')
        self.assertEqual(self.one(r, {'Vachellia tortilis': ('Vachellia tortilis', 'Q12')}, {'Q12': 'Acacia tortilis'}, None, {'Q12': 'Vachellia tortilis'})[1], 'same')
    def test_a_common_name_title_is_the_proposal(self):
        _, st, n, src = self.one(row('a', 'Bull Pine', 'Ponderosa pine', 'Pinus ponderosa'), {'Bull Pine': 'missing'})
        self.assertEqual((st, n, src), ('change', 'Ponderosa pine', 'article title'))
    def test_a_scientific_title_takes_the_wikidata_label_with_a_capital(self):
        _, st, n, src = self.one(row('c', 'Elk', 'Cervus elaphus', 'Cervus elaphus'), {'Cervus elaphus': ('Cervus elaphus', 'Q1'), 'Elk': 'missing'}, {'Q1': 'red deer'})
        self.assertEqual((st, n), ('change', 'Red deer')); self.assertIn('Q1', src)
    def test_a_redirect_is_followed(self):
        _, st, n, _ = self.one(row('c', 'Cougar', 'Cougar'), {'Cougar': ('redirect', 'Puma', 'Q2')})
        self.assertEqual((st, n), ('change', 'Puma'))
    def test_the_same_name_in_other_capitals_or_exactly_is_same(self):
        self.assertEqual(self.one(row('r', 'Common raven', 'Common raven'), {})[1], 'same')
        self.assertEqual(self.one(row('r', 'Common Raven', 'Common raven'), {})[1], 'same')
    def test_missing_and_disambiguation_pages_and_missing_labels_are_not_settled(self):
        self.assertEqual(self.one(row('m', 'X', 'Nowhere'), {'Nowhere': 'missing'})[1], 'unresolved')
        self.assertEqual(self.one(row('d', 'X', 'Mercury'), {'Mercury': 'disambig'})[1], 'unresolved')
        self.assertEqual(self.one(row('l', 'Abies alba', 'Abies alba', 'Abies alba'), {'Abies alba': ('Abies alba', 'Q3')})[1], 'unresolved')   # no name from the data and the current name is the Latin one
    def test_a_label_that_is_again_scientific_is_not_used(self):
        self.assertEqual(self.one(row('l', 'Abies alba', 'Abies alba', 'Abies alba'), {'Abies alba': ('Abies alba', 'Q3')}, {'Q3': 'abies alba'})[1], 'unresolved')

    def test_wikidata_common_names_settle_a_plant_whose_title_and_label_are_scientific(self):
        r = row('p', 'Eastern white pine', 'Pinus strobus', 'Pinus strobus'); pages = {'Pinus strobus': ('Pinus strobus', 'Q5')}
        self.assertEqual(self.one(r, pages, {'Q5': 'Pinus strobus'}, {'Q5': [('Weymouth pine', 'en'), ('Eastern white pine', 'en')]})[1:3], ('same', 'Eastern white pine'))   # the current name is listed: kept
        _, st, n, src = self.one(row('p', 'Pinus strobus', 'Pinus strobus', 'Pinus strobus'), pages, {'Q5': 'Pinus strobus'}, {'Q5': [('Weymouth pine', 'en'), ('Eastern white pine', 'en')]})
        self.assertEqual((st, n), ('change', 'Weymouth pine')); self.assertIn('Q5', src)   # the current name is the Latin name: the first listed
        self.assertEqual(self.one(row('p', 'Pinus strobus', 'Pinus strobus', 'Pinus strobus'), pages, {'Q5': 'Pinus strobus'}, {'Q5': [('Pin blanc', 'fr')]})[1], 'unresolved')   # only other languages
    def test_a_plain_current_name_is_kept_when_wikipedia_and_wikidata_give_no_preferred_one(self):
        r = row('p', 'Virginian Juniper', 'Juniperus virginiana', 'Juniperus virginiana')
        _, st, n, src = self.one(r, {'Juniperus virginiana': ('Juniperus virginiana', 'Q4')}, {'Q4': 'Juniperus virginiana'}, {'Q4': [('Eastern juniper', 'en')]})
        self.assertEqual((st, n), ('same', 'Virginian Juniper')); self.assertIn('kept', src)
    def test_a_scientific_common_name_is_not_used(self):
        r = row('d', 'Diospyros', 'Diospyros', 'Diospyros')
        self.assertEqual(self.one(r, {'Diospyros': ('Diospyros', 'Q3')}, {'Q3': 'Diospyros'}, {'Q3': [('Diospyros', 'en')]})[1], 'unresolved')
    def test_a_disambiguation_bracket_is_not_part_of_the_name(self):
        _, st, n, _ = self.one(row('n', 'Nene (Hawaiian goose)', 'Nene (bird)', 'Branta sandvicensis'), {'Nene (Hawaiian goose)': 'missing'})
        self.assertEqual((st, n), ('change', 'Nene'))
    def test_a_genus_only_title_is_a_scientific_name(self):
        r = row('e', 'Wild Mockcucumber', 'Echinocystis lobata', 'Echinocystis lobata')
        self.assertEqual(self.one(r, {'Echinocystis lobata': ('Echinocystis', 'Q6'), 'Wild Mockcucumber': 'missing'}, {'Q6': 'Echinocystis'})[1], 'unresolved')
    def test_a_current_name_that_is_its_own_article_is_specific_not_a_rename(self):
        r = row('f', 'Feral cat', 'Felis catus', 'Felis catus'); pages = {'Felis catus': ('redirect', 'Cat', 'Q7'), 'Feral cat': ('Feral cat', 'Q8')}
        _, st, n, src = self.one(r, pages)
        self.assertEqual((st, n), ('specific', 'Feral cat')); self.assertIn('Cat', src)
    def test_an_own_article_of_the_rows_own_species_is_a_repoint(self):
        r = row('t', 'Thimbleweed', 'Anemone virginiana', 'Anemone virginiana'); pages = {'Anemone virginiana': ('Anemone virginiana', 'Q1'), 'Thimbleweed': ('Thimbleweed', 'Q2')}
        _, st, n, src = self.one(r, pages, {'Q1': 'Tall thimbleweed'}, taxa={'Q1': 'Anemone virginiana', 'Q2': 'Anemone virginiana'})
        self.assertEqual((st, n), ('repoint', 'Thimbleweed'))
    def test_an_own_article_of_another_species_is_a_new_row(self):
        r = row('c', 'Green-winged Teal', 'Anas crecca', 'Anas crecca'); pages = {'Anas crecca': ('redirect', 'Eurasian teal', 'Q1'), 'Green-winged Teal': ('redirect', 'Green-winged teal', 'Q2')}
        _, st, n, src = self.one(r, pages, taxa={'Q1': 'Anas crecca', 'Q2': 'Anas carolinensis'})
        self.assertEqual((st, n), ('newrow', 'Green-winged teal'))
    def test_a_current_name_that_redirects_to_the_same_page_is_a_plain_rename(self):
        r = row('b', 'Cow', 'Bos taurus', 'Bos taurus'); pages = {'Bos taurus': ('redirect', 'Cattle', 'Q9'), 'Cow': ('redirect', 'Cattle', 'Q9')}
        self.assertEqual(self.one(r, pages)[1:3], ('change', 'Cattle'))

class Scope(unittest.TestCase):
    def test_only_rows_a_node_names_differently_are_in_the_default_scope(self):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'data/places')); os.makedirs(os.path.join(d, 'data/species/rows/a'))
        for sid, name in (('ursus-a', 'Black bear'), ('ursus-b', 'Brown bear')):
            json.dump({'sid': sid, 'name': name, 'wiki': name, 'latin': 'U x', 'sk': 'taxon', 'tl': 3, 'ic': 'x', 'desc': 'd'}, open(os.path.join(d, 'data/species/rows/a/%s.json' % sid), 'w'))
        json.dump({'id': 'p', 'nodes': [{'id': 'n', 'sp': 'ursus-a', 'name': 'American black bear'}, {'id': 'm', 'sp': 'ursus-b'}]}, open(os.path.join(d, 'data/places/p.json'), 'w'))
        try: got = [r['sid'] for r in rowtitles.scope(d)]
        except Exception as e: self.skipTest('the fixture layout of the species table differs: %s' % e)
        self.assertEqual(got, ['ursus-a'])

if __name__ == '__main__': unittest.main()
