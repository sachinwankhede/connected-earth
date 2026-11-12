import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'jobs'))
import conservation as c

def row(n, i, s): return {'n': {'value': n}, 'i': {'value': 'http://www.wikidata.org/entity/' + i}, 's': {'value': 'http://www.wikidata.org/entity/' + s}}

class T(unittest.TestCase):
    def test_codes_and_names_lowercased(self):
        self.assertEqual(c.parse([row('Ursus arctos', 'Q1', 'Q211005')]), {'ursus arctos': {'c': 'LC', 'q': 'Q1'}})
    def test_unknown_category_dropped(self):
        self.assertEqual(c.parse([row('Foo bar', 'Q2', 'Q3245245')]), {})   # data deficient: nothing to show
    def test_endangered_status_item_maps_to_en(self):
        self.assertEqual(c.parse([row('Foo bar', 'Q2', 'Q96377276')]), {'foo bar': {'c': 'EN', 'q': 'Q2'}})
    def test_unmapped_items_are_counted(self):
        from collections import Counter
        u = Counter(); c.parse([row('Foo bar', 'Q2', 'Q3245245'), row('Baz', 'Q4', 'Q3245245'), row('Ok', 'Q5', 'Q211005')], u)
        self.assertEqual(dict(u), {'Q3245245': 2})
    def test_conflicting_codes_dropped(self):
        self.assertEqual(c.parse([row('Foo bar', 'Q2', 'Q11394'), row('Foo bar', 'Q3', 'Q219127')]), {})
    def test_same_code_twice_kept(self):
        self.assertEqual(c.parse([row('Foo bar', 'Q3', 'Q11394'), row('Foo bar', 'Q2', 'Q11394')])['foo bar']['c'], 'EN')
    def test_query_has_names_and_no_quotes_inside(self):
        q = c.query(['Aa bb', 'Cc "dd'])
        self.assertIn('"Aa bb"', q); self.assertIn('"Cc dd"', q); self.assertIn('wdt:P141', q)

if __name__ == '__main__': unittest.main()
