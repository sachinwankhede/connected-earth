#!/usr/bin/env python3
"""Former names in search (#1061): a row renamed to its Wikipedia name keeps the old name findable. search_vocabulary.json also_called {species id: [names]} feeds the search words of the row."""
import glob, json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

class FormerNames(unittest.TestCase):
    def test_every_key_is_a_species_row_and_every_name_is_text(self):
        sids = set()
        for f in glob.glob(os.path.join(ROOT, 'data/species/rows/*/*.json')):
            with open(f, encoding='utf-8') as h: sids.add(json.load(h)['sid'])
        for sid, names in B.ALSO_CALLED.items():
            self.assertIn(sid, sids, sid + ' is not a species row')
            self.assertTrue(names and all(isinstance(n, str) and n.strip() for n in names), sid)
    def test_the_words_of_an_old_name_and_its_spelling_partner_are_added(self):
        self.assertLessEqual({'gray', 'grey'}, B.also_called_words('canis-lupus'))
        self.assertIn('cow', B.also_called_words('bos-taurus'))
        self.assertEqual(B.also_called_words('a-row-with-no-former-name'), set())

if __name__ == '__main__': unittest.main()
