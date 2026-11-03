"""The CI change classifier: which checks each kind of change must run."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build'))
from ci_changes import classify

class ChangeKinds(unittest.TestCase):
    def test_kinds(self):
        cases = [
            (['src/app.html'], (True, False, False)),
            (['build/build.py', 'docs/STATE.md'], (True, False, False)),
            (['tests/app/place.test.mjs'], (True, False, False)),
            (['.github/workflows/ci.yml'], (False, True, False)),
            (['.github/workflows/pages.yml'], (False, True, False)),
            (['build/ci_changes.py', 'tests/jobs/ci_changes_test.py'], (False, False, True)),
            (['build/live_check.py', 'tests/jobs/live_check_test.py'], (False, False, True)),
            (['build/ci_changes.py', 'src/app.html'], (True, False, True)),
            (['data/places/yellowstone.json', 'photos/species_hosted.json'], (False, True, False)),
            (['tests/data/about.test.mjs'], (False, True, False)),
            (['jobs/about.py', 'jobs/syncstep.sh'], (False, False, True)),
            (['tests/jobs/sync_test.py', 'build/state.py'], (False, False, True)),
            (['lib/photo_registry.py'], (False, True, True)),
            (['docs/ARCHITECTURE.md', 'CLAUDE.md', '.github/workflows/data-about.yml', 'jobs/names.json', 'jobs/reports/x.md'], (False, False, False)),
            (['data/places/a.json', 'src/app.html'], (True, True, False)),
            (['something/new.bin'], (True, False, False)),
        ]
        for paths, want in cases: self.assertEqual(classify(paths), want, paths)

if __name__ == '__main__': unittest.main()
