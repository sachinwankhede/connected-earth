#!/usr/bin/env python3
import datetime
from email.message import Message
import os
import struct
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import photo_registry
import wm


class PhotoRegistryTests(unittest.TestCase):
    def test_expiring_negative_cache_uses_capped_backoff(self):
        now = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
        permanent = photo_registry.negative_entry("nophoto", 1, now)
        transient = photo_registry.negative_entry("network", 8, now)
        self.assertEqual(permanent["expiresAt"], "2025-06-30T00:00:00+00:00")
        self.assertEqual(transient["expiresAt"], "2025-01-08T00:00:00+00:00")
        self.assertTrue(photo_registry.cache_active(permanent, now))
        self.assertFalse(photo_registry.cache_active(permanent, now + datetime.timedelta(days=181)))
        self.assertFalse(photo_registry.cache_active("nophoto", now))

    def test_failure_classification_keeps_transient_errors_out_of_permanent_cache(self):
        self.assertEqual(photo_registry.failure_class("nophoto"), "permanent")
        self.assertEqual(photo_registry.failure_class("notphoto"), "permanent")
        self.assertEqual(photo_registry.failure_class("network"), "transient")
        self.assertEqual(photo_registry.failure_class("source-rejected"), "transient")
        self.assertEqual(photo_registry.failure_class("", 404), "permanent")
        self.assertEqual(photo_registry.failure_class("", 503), "transient")

    def test_image_metadata_comes_from_signature_not_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "image.jpg")
            with open(path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + struct.pack(">II", 23, 17))
            self.assertEqual(photo_registry.image_info(path), ("image/png", (23, 17)))

    def test_species_url_validation_accepts_wikimedia_direct_urls_only(self):
        self.assertTrue(photo_registry.safe_species_asset("https://upload.wikimedia.org/wikipedia/commons/a.jpg"))
        self.assertTrue(photo_registry.safe_species_asset("2/2f/a.jpg/330px-a.jpg"))
        self.assertFalse(photo_registry.safe_species_asset("http://upload.wikimedia.org/a.jpg"))
        self.assertFalse(photo_registry.safe_species_asset("https://example.com/a.jpg"))
        self.assertFalse(photo_registry.safe_species_asset("../a.jpg"))

    def test_wikimedia_retry_after_is_bounded(self):
        headers = Message()
        headers["Retry-After"] = "301"
        error = urllib.error.HTTPError("https://en.wikipedia.org/api", 429, "throttled", headers, None)
        with patch.object(wm.urllib.request, "urlopen", side_effect=error), patch.object(wm.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "retry-after exceeds bounded wait"):
                wm.get("https://en.wikipedia.org/api")


if __name__ == "__main__":
    unittest.main()
