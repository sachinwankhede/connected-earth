#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import hostphotos as h


class HostPhotosTests(unittest.TestCase):
    def test_five_added_licences_are_free(self):
        for lic in ("Copyrighted free use", "No restrictions", "FAL", "Free Art License", "KOGL Type 1", "LGPL", "CC BY-SA 4.0", "Public domain"):
            self.assertTrue(h.FREE.match(lic), lic)

    def test_non_free_licences_stay_blocked(self):
        for lic in ("", "unknown", "Fair use", "All rights reserved", "CC BY-NC 4.0", "CC BY-NC-SA 3.0", "CC BY-ND 2.0", "KOGL Type 4", "Copyrighted", "Non-free", "GPL"):
            self.assertFalse(h.FREE.match(lic), lic)

    def test_retry_only_removable_reasons(self):
        self.assertTrue(h.retry("no licence found"))
        self.assertTrue(h.retry("KOGL Type 1"))
        self.assertFalse(h.retry("Fair use"))
        self.assertFalse(h.retry("not on Commons"))
        self.assertFalse(h.retry("download failed"))

    def test_commons_file_from_each_path_shape(self):
        self.assertEqual(h.commons_file("4/42/Opuntia%2C_b.jpg/330px-Opuntia%2C_b.jpg"), "Opuntia,_b.jpg")
        self.assertEqual(h.commons_file("https://upload.wikimedia.org/wikipedia/commons/5/5c/Achnatherum_hymenoides_-_Ricegrass.jpg"), "Achnatherum_hymenoides_-_Ricegrass.jpg")
        self.assertEqual(h.commons_file("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/A.jpg/330px-A.jpg"), "A.jpg")
        self.assertIsNone(h.commons_file("https://thumb.wikimedia.org/wikipedia/en/thumb/0/07/Pallid_Bat.jpg/330px-Pallid_Bat.jpg"))

    def test_thumb_path(self):
        self.assertEqual(h.thumb_path("4/42/A.jpg/330px-A.jpg"), "4/42/A.jpg/330px-A.jpg")
        self.assertEqual(h.thumb_path("https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg"), "5/5c/A.jpg/330px-A.jpg")
        self.assertEqual(h.thumb_path("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/A.jpg/330px-A.jpg"), "5/5c/A.jpg/330px-A.jpg")


if __name__ == "__main__":
    unittest.main()
