// The park-name matching rules (jobs/wikinames.py) must keep accepting typo fixes and rejecting look-alikes (other state, far away, not a park page).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';

test('wikinames matching rules pass their own checks', () => {
  const out = execFileSync('python3', ['jobs/wikinames.py', '--selftest'], { encoding: 'utf8' });
  assert.ok(/ok\s+typo fixed/.test(out) && !/FAIL/.test(out), out);
});
