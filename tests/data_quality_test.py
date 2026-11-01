#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build.data_quality import report


class DataQualityReportTest(unittest.TestCase):
    def test_report_counts_metadata_outlines_and_unresolved_endpoints(self):
        with tempfile.TemporaryDirectory() as root:
            for directory in ("photos/places", "photos", "data/outlines", "data"):
                os.makedirs(os.path.join(root, directory), exist_ok=True)

            valid_photo = {
                "mt": "image/jpeg",
                "width": 640,
                "height": 480,
                "sha256": "a" * 64,
                "a": "Photographer",
                "l": "CC BY 4.0",
                "p": "https://commons.wikimedia.org/wiki/File:Example.jpg",
            }
            self.write_json(root, "photos/places/places.json", {
                "Complete": valid_photo,
                "Incomplete": {"a": "Unknown", "sha256": 5},
            })
            self.write_json(root, "photos/species.json", {"Legacy species": ["image.jpg", "Species"]})
            self.write_json(root, "data/links.json", {
                "order": ["eco1", "eco2"],
                "cross": [
                    {"id": "resolved", "ends": [
                        {"eco": "eco1", "node": "hare"},
                        {"eco": "eco2", "node": "fox"},
                    ]},
                    {"id": "unresolved", "ends": [
                        {"eco": "eco1", "node": "missing"},
                        {"eco": "unknown", "node": "fox"},
                    ]},
                ],
            })
            self.write_json(root, "data/eco1.json", {"nodes": [{"id": "hare"}]})
            self.write_json(root, "data/eco2.json", {"nodes": [{"id": "fox"}]})
            with open(os.path.join(root, "data/outlines/eco1.json"), "w", encoding="utf-8") as outline:
                outline.write("{}")

            output = report(root)

        self.assertIn("| Place-photo metadata fields present | 1/2 |", output)
        self.assertIn("| Place outlines present | 1/2 |", output)
        self.assertIn("| Unresolved cross-place link endpoints | 2/4 |", output)
        self.assertIn("Species-photo attribution metadata | unavailable (1 legacy candidates)", output)
        self.assertIn("sets no quality thresholds", output)

    @staticmethod
    def write_json(root, relative_path, value):
        with open(os.path.join(root, relative_path), "w", encoding="utf-8") as output:
            json.dump(value, output)


if __name__ == "__main__":
    unittest.main()
