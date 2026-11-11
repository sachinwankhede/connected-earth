"""Tests that all network hosts and licences in data jobs, build tools, shell scripts,
and shared libraries are approved in lib/allowed_sources.json, that downloads route
through lib/fetch.py, and that no URLs are built dynamically from variables."""

import glob
import json
import os
import re
import sys
import unittest
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import fetch


class AllowedSourcesTest(unittest.TestCase):
    def test_allowed_sources_file_exists_and_per_source_licences(self):
        config_path = os.path.join(ROOT, 'lib', 'allowed_sources.json')
        self.assertTrue(os.path.isfile(config_path), 'lib/allowed_sources.json must exist')
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn('sources', data, 'lib/allowed_sources.json must define sources')
        self.assertIn('hosts', data, 'lib/allowed_sources.json must define hosts')

        sources = data['sources']
        # Picture rule (#421): Wikimedia CC0, CC BY, CC BY-SA, public domain; GBIF CC0 and CC BY only
        self.assertIn('Wikimedia', sources)
        self.assertEqual(
            sorted(sources['Wikimedia']['allowed_licences']),
            ['CC BY', 'CC BY-SA', 'CC0', 'Public domain'],
            'Wikimedia allows CC0, CC BY, CC BY-SA and public domain (#421)'
        )
        self.assertIn('GBIF', sources)
        self.assertEqual(
            sorted(sources['GBIF']['allowed_licences']),
            ['CC BY', 'CC0'],
            'GBIF must only allow CC0 and CC BY'
        )

    def test_job_lib_build_and_sh_hosts_allowed(self):
        config_path = os.path.join(ROOT, 'lib', 'allowed_sources.json')
        with open(config_path) as f:
            data = json.load(f)
        allowed_hosts = set(data['hosts'])
        unapproved = []

        scan_targets = (
            glob.glob(os.path.join(ROOT, 'jobs', '*.py')) +
            glob.glob(os.path.join(ROOT, 'lib', '*.py')) +
            glob.glob(os.path.join(ROOT, 'build', '*.py')) +
            glob.glob(os.path.join(ROOT, 'jobs', '*.sh'))
        )

        for p in sorted(scan_targets):
            with open(p) as f:
                content = f.read()
            # Normalize regex escaped dots in URL patterns (e.g. en\.wikipedia\.org)
            normalized = content.replace(r'\.', '.')
            urls = re.findall(r'https?://[a-zA-Z0-9_./%-]+', normalized)
            for u in urls:
                parsed = urllib.parse.urlparse(u)
                host = parsed.hostname
                if not host:
                    continue
                if host not in allowed_hosts:
                    unapproved.append((os.path.relpath(p, ROOT), host, u))

        self.assertEqual(
            unapproved,
            [],
            'Unapproved network hosts found. Adding a host requires owner approval in lib/allowed_sources.json: %r' % unapproved
        )

    def test_no_urls_built_from_variables(self):
        """Fails if any URL is dynamically constructed from variable schemes or hosts,
        which would evade static source checks."""
        scan_targets = (
            glob.glob(os.path.join(ROOT, 'jobs', '*.py')) +
            glob.glob(os.path.join(ROOT, 'lib', '*.py')) +
            glob.glob(os.path.join(ROOT, 'build', '*.py')) +
            glob.glob(os.path.join(ROOT, 'jobs', '*.sh'))
        )

        dynamic_url_patterns = [
            (re.compile(r"f[\"']https?://\{"), "f-string variable interpolation in URL scheme/host"),
            (re.compile(r"[\"']https?://[\"']\s*\+"), "concatenation of scheme to variable"),
            (re.compile(r"[\"']https?://%s[\"']"), "% format string in URL scheme/host"),
            (re.compile(r"[\"']https?://\{\}[\"']"), "format() string in URL scheme/host"),
            (re.compile(r"https?://\$[A-Za-z0-9_{]"), "shell variable in URL scheme/host"),
            (re.compile(r"\b(?:curl|wget)\b.*\$[A-Za-z0-9_{]"), "curl/wget with variable target"),
        ]

        violations = []
        for p in sorted(scan_targets):
            # allowed_sources_test itself contains pattern strings, so skip inspecting its test regexes
            if os.path.basename(p) == 'allowed_sources_test.py':
                continue
            with open(p) as f:
                for line_num, line in enumerate(f, 1):
                    for pat, desc in dynamic_url_patterns:
                        if pat.search(line):
                            violations.append((os.path.relpath(p, ROOT), line_num, desc, line.strip()))

        self.assertEqual(
            violations,
            [],
            'URLs built from variables are forbidden. Hosts must be static and approved: %r' % violations
        )

    def test_lib_fetch_runtime_guard(self):
        """Verifies that lib/fetch.py refuses unlisted hosts at run time."""
        # Allowed host should pass
        host = fetch.check_url('https://api.gbif.org/v1/species/match?name=Puma')
        self.assertEqual(host, 'api.gbif.org')

        # Unlisted host should be rejected with PermissionError
        with self.assertRaises(PermissionError):
            fetch.check_url('https://unapproved-malicious-site.example.com/data.json')

        # Non http/https scheme should be rejected
        with self.assertRaises(PermissionError):
            fetch.check_url('ftp://upload.wikimedia.org/file.jpg')

    def test_wm_routes_through_fetch(self):
        """Verifies that jobs/wm.py imports and routes through lib/fetch.py."""
        wm_path = os.path.join(ROOT, 'jobs', 'wm.py')
        with open(wm_path) as f:
            content = f.read()
        self.assertIn('import fetch', content, 'jobs/wm.py must import lib/fetch.py')
        self.assertIn('fetch.urlopen', content, 'jobs/wm.py must route downloads through fetch.urlopen')


    def test_no_download_bypasses_the_guard(self):
        """Every download goes through lib/fetch.py, which refuses unlisted hosts when the script runs. A script that opens the network itself would skip that."""
        exempt = {os.path.join('build', 'live_check.py')}   # checks our own live site, not a data source
        pat = re.compile(r'urlopen|urlretrieve|\brequests\.|http\.client|socket\.create_connection|\bcurl\b|\bwget\b')
        bad = []
        files = sorted(glob.glob(os.path.join(ROOT, 'jobs', '*.py')) + glob.glob(os.path.join(ROOT, 'jobs', '*.sh')) + glob.glob(os.path.join(ROOT, 'build', '*.py')) + glob.glob(os.path.join(ROOT, 'lib', '*.py')))
        for p in files:
            rel = os.path.relpath(p, ROOT)
            if rel in exempt or rel == os.path.join('lib', 'fetch.py'):
                continue
            for n, line in enumerate(open(p, encoding='utf-8'), 1):
                code = line.split('#', 1)[0]
                if pat.search(code) and 'fetch.urlopen' not in code:
                    bad.append('%s:%d: %s' % (rel, n, line.strip()[:100]))
        self.assertEqual(bad, [], 'Open the network through lib/fetch.py (fetch.urlopen, fetch_json, fetch_bytes), not directly: %r' % bad)

if __name__ == '__main__':
    unittest.main()
