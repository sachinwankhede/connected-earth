#!/usr/bin/env python3
"""#648: the source name of a species picture credit is data. Every credit whose page is not on Commons carries `s`, and a Commons credit has none (the app default is Wikimedia Commons)."""
import json, os, sys, unittest, urllib.parse
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import species_pics   # the credits by species id, from either shape on disk (#934)


class CreditSourceData(unittest.TestCase):
    def test_every_credit_off_commons_names_its_source(self):
        meta = {t: species_pics.credit(r) for t, r in species_pics.load(ROOT)['pics'].items()}
        bad = []
        for t, c in meta.items():
            host = (urllib.parse.urlsplit(c.get('p') or '').hostname or '').lower()
            on_commons = host == 'commons.wikimedia.org'
            if on_commons and 's' in c: bad.append('%s: Commons credit has a source name' % t)
            if not on_commons and not c.get('s'): bad.append('%s: no source name (page %s)' % (t, c.get('p')))
        self.assertEqual(bad[:10], [])


if __name__ == '__main__':
    unittest.main()
