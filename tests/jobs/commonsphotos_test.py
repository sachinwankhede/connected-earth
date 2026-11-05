#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import commonsphotos as c


class CommonsPhotosTests(unittest.TestCase):
    def test_open_licences_pass(self):
        for lic in ("CC0", "CC0 1.0", "CC BY 2.0", "CC BY 4.0", "CC BY-SA 3.0", "CC BY-SA 4.0", "CC BY-SA 2.5 ca", "CC-BY-SA-3.0", "Public domain", "PD", "cc by 4.0"):
            self.assertTrue(c.open_licence(lic), lic)

    def test_closed_licences_stay_out(self):
        for lic in ("", "unknown", "CC BY-NC 4.0", "CC BY-NC-SA 3.0", "CC BY-ND 2.0", "CC BY-NC-ND 4.0", "GFDL", "GFDL 1.2", "Fair use", "All rights reserved", "Copyrighted free use", "LGPL", "KOGL Type 1"):
            self.assertFalse(c.open_licence(lic), lic)

    def test_image_names_prefer_preferred_and_drop_deprecated_and_non_photos(self):
        def cl(v, rank='normal'): return {'rank': rank, 'mainsnak': {'datavalue': {'value': v}}}
        got = c.image_names([cl('A normal.jpg'), cl('Old.jpg', 'deprecated'), cl('Best.jpg', 'preferred'), cl('Range map of X.png'), cl('Logo.svg')])
        self.assertEqual(got, ['Best.jpg', 'A normal.jpg'])
        self.assertEqual(c.image_names(None), [])

    def test_manifest_entry_matches_the_speciesphotos_shape(self):
        u = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Aardwolf%2C_Kenya.jpg/330px-Aardwolf%2C_Kenya.jpg'
        self.assertEqual(c.manifest_entry(u, 'Acalypha radians'), ['2/2f/Aardwolf%2C_Kenya.jpg/330px-Aardwolf%2C_Kenya.jpg', 'Acalypha_radians'])
        self.assertIsNone(c.manifest_entry('https://example.com/a.jpg', 'X'))
        self.assertIsNone(c.manifest_entry('', 'X'))
        self.assertIsNone(c.manifest_entry('https://upload.wikimedia.org/wikipedia/en/thumb/a/ab/X.jpg/330px-X.jpg', 'X'), 'only Commons thumbnails')

    def test_hostphotos_can_read_what_we_write(self):
        import hostphotos as h
        e = c.manifest_entry('https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Aardwolf%2C_Kenya.jpg/330px-Aardwolf%2C_Kenya.jpg', 'X')
        self.assertEqual(h.commons_file(e[0]), 'Aardwolf,_Kenya.jpg')
        self.assertEqual(h.thumb_path(e[0]), e[0])


if __name__ == "__main__":
    unittest.main()
