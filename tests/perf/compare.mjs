// compare.mjs: compares two sets of perf.mjs results (one JSON file per run, from `perf.mjs --runs 1`), side A against side B.
//   node tests/perf/compare.mjs --a out/a --b out/b --label-a main --label-b my-branch --md out/compare.md
// Each side's value is the median across its runs. A mark flags a difference of more than 15% and more than 20 (ms or KB); lower is better for every metric.
import fs from 'node:fs';
import path from 'node:path';
import { INITIAL_STAGE_DEFINITIONS } from './metrics.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const DIR_A = arg('a'), DIR_B = arg('b'), LA = arg('label-a', 'A'), LB = arg('label-b', 'B'), MD = arg('md', 'compare.md');
if (!DIR_A || !DIR_B) { console.error('usage: compare.mjs --a DIR --b DIR [--label-a X --label-b Y --md FILE]'); process.exit(2); }

const median = (xs) => { xs = xs.filter(Number.isFinite).sort((p, q) => p - q); return xs.length ? xs[Math.floor(xs.length / 2)] : null; };
const RETURNING_LABELS = { fcp: 'First contentful paint', domInteractive: 'DOM interactive', load: 'Load event', mapLoaded: 'Map loaded', blockingMs: 'Blocking time before map loaded' };

function readRuns(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => /^run-.*\.json$/.test(f)).sort().flatMap((f) => {
    try { return [JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'))]; } catch (e) { console.error('skipping', f, e.message); return []; }
  });
}

// one flat { metric name -> number } per profile of one run result
function flatten(s) {
  const m = {};
  for (const [k, v] of Object.entries(s)) if (typeof v === 'number') m[k] = v;
  const phases = (s.initialLoad && s.initialLoad.phases) || {};
  for (const [k, v] of Object.entries(phases)) if (v && Number.isFinite(v.p50)) m['stage: ' + INITIAL_STAGE_DEFINITIONS[k].label + ' (ms)'] = v.p50;
  const lt = s.initialLoad && s.initialLoad.longTasks;
  if (lt && lt.blockingMs && Number.isFinite(lt.blockingMs.p50)) m['long-task blocking before first photo (ms)'] = lt.blockingMs.p50;
  const rv = s.returning && s.returning.metrics;
  if (rv) for (const [k, label] of Object.entries(RETURNING_LABELS)) if (rv[k] && Number.isFinite(rv[k].p50)) m['returning: ' + label + ' (ms)'] = rv[k].p50;
  return m;
}

const A = readRuns(DIR_A), B = readRuns(DIR_B);
const fmt = (v) => (v == null ? 'n/a' : Math.round(v).toString());
let md = `## Perf comparison: ${LA} (A) vs ${LB} (B)\n\nMedian of ${A.length} run(s) for A and ${B.length} for B, alternating A and B on the same runner and served the same way, so only the difference between them is meaningful; absolute numbers are not comparable with live-site runs. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Lower is better. ⚠ = B more than 15% and 20 worse than A; ✓ = B more than 15% and 20 better. Small samples: treat a single flag as a lead, not proof.\n`;
let worse = 0, better = 0;
if (!A.length || !B.length) md += `\nNo results on one side (A: ${A.length}, B: ${B.length}), so there is nothing to compare.\n`;
else {
  for (const profile of ['phone', 'desktop']) {
    const a = A.map((r) => r[profile] && flatten(r[profile])).filter(Boolean), b = B.map((r) => r[profile] && flatten(r[profile])).filter(Boolean);
    const names = [...new Set([...a, ...b].flatMap((x) => Object.keys(x)))];
    md += `\n### ${profile}\n\n| Metric | ${LA} (A) | ${LB} (B) | Change |\n|---|---:|---:|---:|\n`;
    for (const n of names) {
      const av = median(a.map((x) => x[n])), bv = median(b.map((x) => x[n]));
      let change = '';
      if (av != null && bv != null && av > 0) {
        const d = (bv - av) / av, diff = bv - av;
        const flag = d > 0.15 && diff > 20 ? ' ⚠' : d < -0.15 && diff < -20 ? ' ✓' : '';
        if (flag === ' ⚠') worse++;
        if (flag === ' ✓') better++;
        change = (d > 0 ? '+' : '') + Math.round(d * 100) + '%' + flag;
      }
      md += `| ${n} | ${fmt(av)} | ${fmt(bv)} | ${change} |\n`;
    }
  }
  md += `\n${better} metric(s) flagged better, ${worse} flagged worse.\n`;
}
fs.writeFileSync(MD, md);
console.log(md);
