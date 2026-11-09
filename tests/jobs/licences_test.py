import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import licences as L
import gbifphotos as g

class LicenceRuleTests(unittest.TestCase):
    def test_canonical_names(self):
        cases = {"CC0 1.0": "CC0", "CC BY 4.0": "CC BY", "CC-BY-3.0": "CC BY", "CC BY-SA 2.5 ca": "CC BY-SA", "CC-BY-SA-4.0": "CC BY-SA", "cc by 4.0": "CC BY", "PD": "Public domain", "Public domain": "Public domain"}
        for t, c in cases.items(): self.assertEqual(L.canonical(t), c, t)

    def test_not_canonical(self):
        for t in ("", None, "GFDL", "LGPL", "FAL", "KOGL Type 1", "Attribution", "No restrictions", "Copyrighted free use", "CC BY-NC 4.0", "CC BY-ND 2.0", "CC BY-NC-SA 3.0", "CC BY-NC-ND 4.0"):
            self.assertIsNone(L.canonical(t), t)

    def test_ok_per_source(self):
        self.assertTrue(L.ok('Wikimedia', 'CC BY-SA 4.0'))
        self.assertFalse(L.ok('GBIF', 'CC BY-SA 4.0'))
        self.assertTrue(L.ok('GBIF', 'CC BY 4.0'))
        self.assertFalse(L.ok('Wikimedia', 'GFDL'))

    def test_gbif_licences_are_inside_the_rule(self):
        for url, (name, _) in g.LICENCES.items():
            self.assertTrue(L.ok('GBIF', name), name)

if __name__ == '__main__': unittest.main()
