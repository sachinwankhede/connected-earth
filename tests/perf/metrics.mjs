export const INITIAL_STAGE_DEFINITIONS = {
  domInteractive: { label: 'DOM interactive', method: 'Navigation Timing' },
  domContentLoaded: { label: 'DOMContentLoaded', method: 'Navigation Timing' },
  load: { label: 'Load event', method: 'Navigation Timing' },
  firstContentfulPaint: { label: 'First contentful paint', method: 'Paint Timing' },
  appDataReady: { label: 'App data ready', method: '20 ms poll of window.__M.ecoIds()' },
  cardsDomRendered: { label: 'Initial cards in DOM', method: '20 ms DOM-state poll; first populated #cards card' },
  mapStyleReady: { label: 'Map style ready', method: '20 ms poll of window.__M.styleReady' },
  mapFirstTileResponse: { label: 'First map tile response', method: 'Resource Timing responseEnd for a tile URL' },
  mapLoaded: { label: 'Map loaded', method: '20 ms poll of MapLibre map.loaded()' },
  photoHoldRelease: { label: 'Photo hold released', method: '20 ms poll of window.__M.photoGo' },
  firstVisiblePhotoLoad: { label: 'First visible photo loaded', method: 'Image load event for a photo intersecting the viewport' },
  firstVisiblePhotoDecode: { label: 'First visible photo decoded', method: 'HTMLImageElement.decode() resolution' },
};

const percentile = (values, p) => {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const i = (sorted.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
};

export function summarizeInitialStages(runs, attemptedRuns = runs.length) {
  const completedRuns = runs.length;
  const phases = Object.fromEntries(Object.entries(INITIAL_STAGE_DEFINITIONS).map(([key, definition]) => {
    const values = runs.map((run) => run.initialStages && run.initialStages[key]).filter(Number.isFinite);
    return [key, {
      samples: values.length,
      failures: Math.max(0, attemptedRuns - values.length),
      p50: percentile(values, 0.5),
      p95: percentile(values, 0.95),
      method: definition.method,
    }];
  }));
  const longTaskRuns = runs.map((run) => run.initialLongTasks).filter(Boolean);
  const summarize = (key) => {
    const values = longTaskRuns.map((run) => run[key]).filter(Number.isFinite);
    return { p50: percentile(values, 0.5), p95: percentile(values, 0.95) };
  };
  return {
    attemptedRuns,
    completedRuns,
    failedRuns: Math.max(0, attemptedRuns - completedRuns),
    phases,
    longTasks: {
      samples: longTaskRuns.length,
      failures: Math.max(0, attemptedRuns - longTaskRuns.length),
      count: summarize('count'),
      durationMs: summarize('durationMs'),
      blockingMs: summarize('blockingMs'),
    },
  };
}
