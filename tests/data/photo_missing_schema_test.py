"""#887 step 5b: a place-photo miss records its inputs (lib/photo_registry.negative_entry), and build/schemas/photo-missing.schema.json must accept that record. Without this the weekly data-placepictures run wrote misses the validator then refused (run 44095351082, 17 Nov)."""
import datetime, json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import photo_registry

SCHEMA = os.path.join(ROOT, 'build', 'schemas', 'photo-missing.schema.json')

class MissSchema(unittest.TestCase):
    def setUp(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        self.js = jsonschema
        self.schema = json.load(open(SCHEMA, encoding='utf-8'))
        self.now = datetime.datetime(2026, 11, 17, 12, 0, tzinfo=datetime.timezone.utc)

    def test_miss_with_inputs_is_accepted(self):
        inp = photo_registry.place_inputs({'lat': 44.12345, 'lon': -72.5, 'name': 'X Park', 'title': 'X_Park'})
        entry = photo_registry.negative_entry('nophoto', 1, self.now, inp)
        self.js.validate({'vtx': entry}, self.schema)

    def test_miss_without_inputs_is_still_accepted(self):
        entry = photo_registry.negative_entry('nophoto', 1, self.now)
        self.js.validate({'vtx': entry}, self.schema)

    def test_unknown_field_inside_inputs_is_refused(self):
        inp = photo_registry.place_inputs({'lat': 44.1, 'lon': -72.5, 'name': 'X', 'title': 'X'})
        inp['extra'] = 1
        entry = photo_registry.negative_entry('nophoto', 1, self.now, inp)
        with self.assertRaises(self.js.ValidationError):
            self.js.validate({'vtx': entry}, self.schema)

if __name__ == '__main__':
    unittest.main()
