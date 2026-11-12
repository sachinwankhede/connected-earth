import os, json, unittest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
CODES = {'LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX'}

class ConservationInSpeciesFiles(unittest.TestCase):
    """#680: the build carries the Wikidata status code into api/species/<id>.json as `cs`; a species with no status has no `cs`."""
    def test_cs_is_a_known_code_and_matches_the_data_file(self):
        d = os.path.join(ROOT, 'api', 'species')
        if not os.path.isdir(d): self.skipTest('no build output (api/species/) yet')
        cons = json.load(open(os.path.join(ROOT, 'data', 'species', 'conservation.json')))
        seen = 0
        for f in os.listdir(d):
            s = json.load(open(os.path.join(d, f)))
            if 'cs' not in s: continue
            seen += 1
            self.assertIn(s['cs'], CODES, f)
            self.assertEqual(cons[s['l'].lower()]['c'], s['cs'], f)
        self.assertGreater(seen, 0, 'no species file carries a status')

if __name__ == '__main__':
    unittest.main()
