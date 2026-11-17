"""#887: a record shape and its written contract (build/schemas/*.schema.json) must change together.
Every schema must be listed in WRITERS below. A schema whose records are written by a lib/ writer has a sample made by that writer, and the test validates it against the schema, so a writer that adds a field the schema refuses (the miss `inputs` of 17 Nov, #1051) fails here, in the pull request, and not a week later in a data job. A schema with no lib writer says where its records come from; the committed file is still checked by build/validate_data.py. A new schema that is not listed fails the test, so nobody can add one and forget this check."""
import datetime, json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
SCHEMAS = os.path.join(ROOT, 'build', 'schemas')
NOW = datetime.datetime(2026, 11, 17, 12, 0, tzinfo=datetime.timezone.utc)

def photo_missing():
    import photo_registry as pr
    inp = pr.place_inputs({'lat': 44.12345, 'lon': -72.5, 'name': 'X Park', 'title': 'X_Park'})
    nopoint = pr.place_inputs({'name': 'Y Park'})   # a place with no point: lat and lon are null
    return {'with-inputs': pr.negative_entry('nophoto', 1, NOW, inp), 'no-point': pr.negative_entry('notfree', 2, NOW, nopoint),
            'without-inputs': pr.negative_entry('wrongpage', 3, NOW)}

# schema kind -> a function returning {key: record} made by the real writer, or a string saying where the records come from
WRITERS = {
    'photo-missing': photo_missing,   # lib/photo_registry.negative_entry, used by the place and species picture writers
    'about': 'jobs/about.py', 'diets': 'jobs/ and build/species.py (data/diets)', 'geo': 'data/geo/geo.json, a source file',
    'journey': 'journey files (jobs/ and the research branch)', 'journey-config': 'data/journeys/config.json, a source file',
    'land': 'data/geo/land.json, a source file', 'names': 'jobs/names.json (jobs/)', 'outline': 'jobs/bounds.py and jobs/bounds_more.py',
    'species-row': 'build/species.py', 'summaries': 'data/text/summaries.json (jobs/)', 'taxonomy': 'jobs/ (taxonomy)',
    'taxonomy-manual': 'data/species/taxonomy_manual.json, edited with the taxonomy tools', 'taxonomy-review': 'jobs/ (taxonomy review)',
}

class WriterSchemas(unittest.TestCase):
    def test_every_schema_is_listed(self):
        kinds = sorted(f[:-len('.schema.json')] for f in os.listdir(SCHEMAS) if f.endswith('.schema.json'))
        self.assertEqual(sorted(WRITERS), kinds, 'every build/schemas/<kind>.schema.json needs an entry in WRITERS (a lib writer sample, or where its records come from), and no entry may name a schema that is gone')

    def test_lib_writer_output_matches_its_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        for kind, made in WRITERS.items():
            if not callable(made): continue
            schema = json.load(open(os.path.join(SCHEMAS, kind + '.schema.json'), encoding='utf-8'))
            for label, record in made().items():
                try:
                    jsonschema.validate({'k': record} if kind == 'photo-missing' else record, schema)
                except jsonschema.ValidationError as e:
                    self.fail('%s: the writer made a %s record the schema refuses: %s' % (kind, label, e.message[:200]))

if __name__ == '__main__':
    unittest.main()
