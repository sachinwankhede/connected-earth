import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
// The sync rules of the data jobs (pipeline/syncmain.py), tried on throwaway git repositories.
test('data sync rules', () => {
  const r = spawnSync('python3', ['-m', 'unittest', 'tests/sync_test.py', '-v'], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stdout + r.stderr);
});
