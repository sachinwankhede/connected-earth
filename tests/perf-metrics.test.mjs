import { test } from 'node:test';
import assert from 'node:assert/strict';
import { INITIAL_STAGE_DEFINITIONS, summarizeInitialStages } from './perf/metrics.mjs';

test('initial-load stage summary reports p50/p95, methods, samples, and failures', () => {
  const summary = summarizeInitialStages([
    { initialStages: { appDataReady: 100 }, initialLongTasks: { count: 2, durationMs: 180, blockingMs: 80 } },
    { initialStages: { appDataReady: 200 }, initialLongTasks: { count: 4, durationMs: 260, blockingMs: 160 } },
  ], 3);

  assert.deepEqual(summary, {
    attemptedRuns: 3,
    completedRuns: 2,
    failedRuns: 1,
    phases: Object.fromEntries(Object.entries(INITIAL_STAGE_DEFINITIONS).map(([key, definition]) => [
      key,
      key === 'appDataReady'
        ? { samples: 2, failures: 1, p50: 150, p95: 195, method: definition.method }
        : { samples: 0, failures: 3, p50: null, p95: null, method: definition.method },
    ])),
    longTasks: {
      samples: 2,
      failures: 1,
      count: { p50: 3, p95: 3.9 },
      durationMs: { p50: 220, p95: 256 },
      blockingMs: { p50: 120, p95: 156 },
    },
  });
});

test('initial-load stage summary keeps missing phases explicit when every sample is absent', () => {
  const summary = summarizeInitialStages([{ initialStages: {} }, { initialStages: {} }], 2);

  for (const phase of Object.values(summary.phases)) {
    assert.deepEqual(
      { samples: phase.samples, failures: phase.failures, p50: phase.p50, p95: phase.p95 },
      { samples: 0, failures: 2, p50: null, p95: null },
    );
    assert.ok(phase.method);
  }
  assert.deepEqual(summary.longTasks, {
    samples: 0,
    failures: 2,
    count: { p50: null, p95: null },
    durationMs: { p50: null, p95: null },
    blockingMs: { p50: null, p95: null },
  });

  const failed = summarizeInitialStages([], 2);
  assert.equal(failed.completedRuns, 0);
  assert.equal(failed.failedRuns, 2);
  assert.ok(Object.values(failed.phases).every((phase) => phase.samples === 0 && phase.failures === 2));
});
