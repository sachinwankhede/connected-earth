"""lib/contracts.json is the one place for the rules that jobs, validators and tests share (docs/DATA-PLAN.md step 2)."""
import json, os, re, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import contracts, photo_registry, place_sources, species_sources


class Contracts(unittest.TestCase):
    def test_the_modules_use_the_contract(self):
        self.assertEqual(photo_registry.PERMANENT, set(contracts.PERMANENT_STATUSES))
        self.assertEqual(place_sources.RETRY_DAYS, contracts.SOURCE_RETRY_DAYS)
        self.assertEqual(species_sources.RETRY_DAYS, contracts.SOURCE_RETRY_DAYS)

    def test_retry_windows(self):
        import datetime
        now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        perm = photo_registry.negative_entry('nophoto', now=now)
        self.assertEqual(perm['expiresAt'], (now + datetime.timedelta(days=contracts.PERMANENT_RETRY_DAYS)).isoformat())
        slow = photo_registry.negative_entry('timeout', attempts=50, now=now)
        self.assertEqual(slow['expiresAt'], (now + datetime.timedelta(hours=contracts.TRANSIENT_RETRY_MAX_HOURS)).isoformat())

    def test_schema_accepts_exactly_the_permanent_statuses(self):
        with open(os.path.join(ROOT, 'build', 'schemas', 'photo-missing.schema.json')) as f:
            schema = json.load(f)
        self.assertEqual(set(schema['additionalProperties']['properties']['status']['enum']), set(contracts.PERMANENT_STATUSES))

    def test_story_limits_are_what_the_writer_and_the_place_check_use(self):
        import gemini_stories as g
        self.assertEqual((g.STORY_WORDS, g.WHY_WORDS, g.STORY_CHARS, g.WHY_CHARS), (contracts.STORY_WORDS, contracts.WHY_WORDS, contracts.STORY_CHARS, contracts.WHY_CHARS))
        self.assertLessEqual(contracts.STORY_CHARS[0], contracts.STORY_CHARS[1]); self.assertLessEqual(contracts.WHY_CHARS[0], contracts.WHY_CHARS[1])

    def test_no_second_copy_of_a_shared_number(self):
        """A literal retry window or story limit written again in lib/ or jobs/ is a copy that can drift."""
        pats = [r'RETRY_DAYS\s*=\s*\d', r'STORY_WORDS\s*=\s*\d', r'WHY_WORDS\s*=\s*\d', r'STORY_CHARS\s*=\s*\(', r'WHY_CHARS\s*=\s*\(', r'timedelta\(days=180\)']
        bad = []
        for d in ('lib', 'jobs'):
            for fn in sorted(os.listdir(os.path.join(ROOT, d))):
                if not fn.endswith('.py') or fn == 'contracts.py': continue
                text = open(os.path.join(ROOT, d, fn), encoding='utf-8').read()
                for p in pats:
                    if re.search(p, text): bad.append('%s/%s: %s' % (d, fn, p))
        self.assertEqual(bad, [])


if __name__ == '__main__':
    unittest.main()
