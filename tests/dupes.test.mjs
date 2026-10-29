// The rule that drops a park listed twice under different unit names (pipeline/dupes.py) must keep dropping real twins and keeping look-alikes.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';

test('duplicate-park rules pass their own checks', () => {
  const out = execFileSync('python3', ['pipeline/dupes.py', '--selftest'], { encoding: 'utf8' });
  assert.ok(/ok\s+same park/.test(out) && !/FAIL/.test(out), out);
});
