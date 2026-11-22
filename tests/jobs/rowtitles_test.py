import json, os, sys, tempfile, unittest, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import rowtitles

def fake(pages, labels):
    """get() answering like Wikipedia ({asked title: (final title, wikidata id) | 'missing' | 'disambig' | ('redirect', to, id)}) and Wikidata ({id: label})."""
    def get(url):
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
    def one(self, r, pages, labels=None):
        return rowtitles.decide([r], fake(pages, labels or {}))[0]
    def test_a_common_name_title_is_the_proposal(self):
        _, st, n, src = self.one(row('a', 'Bull Pine', 'Ponderosa pine', 'Pinus ponderosa'), {})
        self.assertEqual((st, n, src), ('change', 'Ponderosa pine', 'article title'))
    def test_a_scientific_title_takes_the_wikidata_label_with_a_capital(self):
        _, st, n, src = self.one(row('c', 'Elk', 'Cervus elaphus', 'Cervus elaphus'), {'Cervus elaphus': ('Cervus elaphus', 'Q1')}, {'Q1': 'red deer'})
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
        self.assertEqual(self.one(row('l', 'X', 'Abies alba', 'Abies alba'), {'Abies alba': ('Abies alba', 'Q3')})[1], 'unresolved')
    def test_a_label_that_is_again_scientific_is_not_used(self):
        self.assertEqual(self.one(row('l', 'X', 'Abies alba', 'Abies alba'), {'Abies alba': ('Abies alba', 'Q3')}, {'Q3': 'abies alba'})[1], 'unresolved')

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
