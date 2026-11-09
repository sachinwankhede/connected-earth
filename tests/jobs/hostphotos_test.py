#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import hostphotos as h


class HostPhotosTests(unittest.TestCase):
    def test_rule_licences_are_hosted(self):
        for lic in ("CC0", "CC BY 4.0", "CC BY-SA 4.0", "CC BY-SA 3.0", "Public domain", "PD"):
            self.assertTrue(h.FREE.match(lic), lic)

    def test_everything_else_stays_blocked(self):
        for lic in ("", "unknown", "Fair use", "All rights reserved", "CC BY-NC 4.0", "CC BY-NC-SA 3.0", "CC BY-ND 2.0", "KOGL Type 1", "KOGL Type 4", "Copyrighted", "Copyrighted free use", "No restrictions", "Attribution", "FAL", "Free Art License", "LGPL", "GFDL", "GPL"):
            self.assertFalse(h.FREE.match(lic), lic)

    def test_retry_only_removable_reasons(self):
        self.assertTrue(h.retry("no licence found"))
        self.assertTrue(h.retry("CC BY-SA 4.0"))
        self.assertFalse(h.retry("KOGL Type 1"))
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


class DownloadTests(unittest.TestCase):
    def run_download(self, u, answers):
        seen = []
        def fake(url, raw=False, tries=6):
            seen.append(url); a = answers.pop(0)
            if isinstance(a, Exception): raise a
            return a
        old = h.wm.get; h.wm.get = fake
        try: return h.download(u), seen
        finally: h.wm.get = old

    def test_a_thumbnail_path_downloads_the_thumbnail_only(self):
        raw, seen = self.run_download("4/42/A.jpg/330px-A.jpg", [b"x"])
        self.assertEqual((raw, seen), (b"x", [h.BASE + "4/42/A.jpg/330px-A.jpg"]))

    def test_a_small_original_falls_back_to_the_original(self):
        u = "https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg"
        raw, seen = self.run_download(u, [RuntimeError("400"), b"orig"])
        self.assertEqual((raw, seen), (b"orig", [h.BASE + "5/5c/A.jpg/330px-A.jpg", u]))

    def test_a_large_original_still_uses_its_thumbnail(self):
        raw, seen = self.run_download("https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg", [b"thumb"])
        self.assertEqual((raw, seen), (b"thumb", [h.BASE + "5/5c/A.jpg/330px-A.jpg"]))
