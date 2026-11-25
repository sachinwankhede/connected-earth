#!/usr/bin/env python3
"""Every picture needs a named author, whatever its licence (owner, 25 Nov, #887): a public domain label with no author is refused like CC BY."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
from place_photos import author_missing

class T(unittest.TestCase):
    def test_refused_without_author(self):
        for lic in ('Public domain', 'CC0', 'CC BY 4.0', 'CC BY-SA 3.0'):
            for a in ('', None, 'Unknown author', 'Unknown'): self.assertTrue(author_missing({'l': lic, 'a': a}), (lic, a))
    def test_kept_with_author(self):
        for lic in ('Public domain', 'CC0', 'CC BY 4.0'): self.assertFalse(author_missing({'l': lic, 'a': 'Jane Doe'}))
if __name__ == '__main__': unittest.main()
