import { chromium } from 'playwright';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const RUNS = Math.max(1, Number(process.argv[process.argv.indexOf('--runs') + 1] || 5));
const ECO = 'yellowstone';
const PROFILES = {
  phone: { viewport: { width: 390, height: 800 }, cpu: 4, net: { offline: false, latency: 150, downloadThroughput: 200000, uploadThroughput: 93750 } },
  desktop: { viewport: { width: 1280, height: 800 }, cpu: 1 },
};

execFileSync('python3', ['build/build.py', '--all'], { cwd: ROOT, stdio: 'inherit' });

const built = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const edits = [
  [
    'function showWeb(id, then, fromJ, fromP) {\n',
    'function showWeb(id, then, fromJ, fromP) {\n    window.__exploreProfile.navStarts.push({ id: id, t: performance.now() });\n',
  ],
  [
    'function loadEco(id) {\n    ECO = ECO_BY[id];',
    'function loadEco(id) {\n    var __ep = { id: id, start: performance.now() };\n    window.__exploreProfile.current = __ep;\n    ECO = ECO_BY[id];',
  ],
  [
    '    build();\n    applyEnv();',
    '    __ep.dataPrepEnd = performance.now();\n    build();\n    __ep.graphBuildEnd = performance.now();\n    applyEnv();',
  ],
  [
    '    configure();\n    for (var i = 0; i < 120; i++) sim.tick();\n    ticked();',
    '    configure();\n    __ep.preTickEnd = performance.now();\n    var __tick = sim.tick, __tickMs = 0, __tickCount = 0;\n    sim.tick = function () { var __t = performance.now(), __r = __tick.apply(this, arguments); __tickMs += performance.now() - __t; __tickCount++; return __r; };\n    var __tickWallStart = performance.now();\n    for (var i = 0; i < 120; i++) sim.tick();\n    __ep.tickWallMs = performance.now() - __tickWallStart;\n    sim.tick = __tick;\n    __ep.tickMs = __tickMs; __ep.tickCount = __tickCount; __ep.tickEnd = performance.now();\n    ticked();\n    __ep.tickedEnd = performance.now();',
  ],
  [
    '    renderPanel();\n    paint();\n    apply();',
    '    __ep.fitGuidesEnd = performance.now();\n    var __panelStart = performance.now(); renderPanel(); __ep.renderPanelMs = performance.now() - __panelStart;\n    var __paintStart = performance.now(); paint(); __ep.paintMs = performance.now() - __paintStart;\n    apply();',
  ],
  [
    '    loadPhotos();\n    \n  }\n\n  /* ---------- Controls ---------- */',
    '    loadPhotos();\n    __ep.end = performance.now();\n    window.__exploreProfile.samples.push(__ep);\n    window.__exploreProfile.current = null;\n    \n  }\n\n  /* ---------- Controls ---------- */',
  ],
  [
    '      loadEco(id); syncHash(); if (then) then();',
    '      loadEco(id); window.__exploreProfile.routeReady.push({ id: id, t: performance.now() }); syncHash(); if (then) then();',
  ],
];
let instrumented = built;
for (const [before, after] of edits) {
  if (!instrumented.includes(before)) throw new Error(`Instrumentation anchor missing: ${before.slice(0, 80)}`);
  instrumented = instrumented.replace(before, after);
}
const contentTypes = { '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\/+/, '') || 'index.html';
  const file = path.resolve(ROOT, rel);
  if (!file.startsWith(ROOT + path.sep)) { res.writeHead(403).end(); return; }
  if (rel === 'index.html') { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }).end(instrumented); return; }
  try { res.writeHead(200, { 'content-type': contentTypes[path.extname(file)] || 'application/octet-stream' }).end(fs.readFileSync(file)); }
  catch { res.writeHead(404).end(); }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}/`;
const browser2 = await chromium.launch({ args: ['--no-sandbox'] });
const rows = {};

for (const [name, profile] of Object.entries(PROFILES)) {
  rows[name] = [];
  for (let run = 0; run < RUNS; run++) {
    const context = await browser2.newContext({ viewport: profile.viewport, serviceWorkers: 'block' });
    const page = await context.newPage();
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    if (profile.cpu > 1) {
      await cdp.send('Emulation.setCPUThrottlingRate', { rate: profile.cpu });
      await cdp.send('Network.emulateNetworkConditions', profile.net);
    }
    await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (route) => route.abort());
    await page.addInitScript(() => {
      window.__exploreProfile = { samples: [], navStarts: [], routeReady: [] };
      window.__webParses = [];
      const json = Response.prototype.json;
      Response.prototype.json = function () {
        const url = this.url, start = performance.now();
        return json.call(this).then((value) => {
          if (/\/webs\/[^/]+\.json$/.test(url)) window.__webParses.push({ url, ms: performance.now() - start, at: performance.now() });
          return value;
        });
      };
    });
    try {
      await page.goto(`${base}#stub&e=${ECO}`, { waitUntil: 'load', timeout: 120000 });
      await page.waitForFunction(() => {
        const m = window.__exploreProfile, v = document.getElementById('webview');
        return m?.routeReady.length && v && !v.hidden && document.getElementById('webload')?.hidden && document.querySelector('#svg .node');
      }, null, { timeout: 90000 });
      const cold = await page.evaluate(() => {
        const m = window.__exploreProfile, n = m.navStarts[0], r = m.routeReady[0], s = m.samples[0];
        const w = performance.getEntriesByType('resource').find((e) => e.name.endsWith(`/webs/${s.id}.json`));
        const j = window.__webParses.find((e) => e.url.endsWith(`/webs/${s.id}.json`));
        return { setup: s, routeReadyMs: r.t - n.t, fetchMs: w ? w.responseEnd - w.startTime : null, parseMs: j?.ms ?? null, transferBytes: w?.transferSize ?? null };
      });
      await page.evaluate(() => document.getElementById('back').click());
      await page.waitForFunction(() => !document.getElementById('pview').hidden && document.querySelector('#pview h2'));
      await page.locator('#pview #pgraph').click();
      await page.waitForFunction(() => window.__exploreProfile.routeReady.length >= 2 && !document.getElementById('webview').hidden && document.getElementById('webload')?.hidden && document.querySelector('#svg .node'));
      const warm = await page.evaluate(() => {
        const m = window.__exploreProfile, n = m.navStarts[1], r = m.routeReady[1], s = m.samples[1];
        const w = performance.getEntriesByType('resource').filter((e) => e.startTime >= n.t && e.name.endsWith(`/webs/${s.id}.json`));
        const j = window.__webParses.filter((e) => e.at >= n.t && e.url.endsWith(`/webs/${s.id}.json`));
        return { setup: s, routeReadyMs: r.t - n.t, fetchCount: w.length, parseCount: j.length };
      });
      rows[name].push({ cold, warm });
    } finally { await context.close(); }
  }
}
await browser2.close();
await new Promise((resolve) => server.close(resolve));

const percentile = (values, p) => {
  const xs = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!xs.length) return null;
  const at = (xs.length - 1) * p, lo = Math.floor(at), hi = Math.ceil(at);
  return xs[lo] + (xs[hi] - xs[lo]) * (at - lo);
};
const summary = {};
for (const [profile, samples] of Object.entries(rows)) {
  summary[profile] = {};
  for (const phase of ['cold', 'warm']) {
    const entries = samples.map((x) => x[phase]);
    const metrics = {
      routeReadyMs: (x) => x.routeReadyMs,
      dataPrepMs: (x) => x.setup.dataPrepEnd - x.setup.start,
      graphBuildMs: (x) => x.setup.graphBuildEnd - x.setup.dataPrepEnd,
      preTickMs: (x) => x.setup.preTickEnd - x.setup.graphBuildEnd,
      tickMs: (x) => x.setup.tickMs,
      tickWallMs: (x) => x.setup.tickWallMs,
      afterTicksMs: (x) => x.setup.tickedEnd - x.setup.tickEnd,
      fitGuidesMs: (x) => x.setup.fitGuidesEnd - x.setup.tickedEnd,
      finalizeMs: (x) => x.setup.end - x.setup.tickEnd,
      renderPanelMs: (x) => x.setup.renderPanelMs,
      paintMs: (x) => x.setup.paintMs,
      totalSetupMs: (x) => x.setup.end - x.setup.start,
    };
    summary[profile][phase] = {};
    for (const [key, get] of Object.entries(metrics)) {
      const values = entries.map(get).filter(Number.isFinite);
      summary[profile][phase][key] = {
        n: values.length,
        p50: +percentile(values, .5).toFixed(2),
        p95: +percentile(values, .95).toFixed(2),
        min: +Math.min(...values).toFixed(2),
        max: +Math.max(...values).toFixed(2),
      };
    }
    summary[profile][phase].tickCounts = entries.map((x) => x.setup.tickCount);
    if (phase === 'cold') {
      summary[profile][phase].fetchMs = entries.map((x) => x.fetchMs);
      summary[profile][phase].parseMs = entries.map((x) => x.parseMs);
      summary[profile][phase].transferBytes = entries.map((x) => x.transferBytes);
    } else {
      summary[profile][phase].fetchCounts = entries.map((x) => x.fetchCount);
      summary[profile][phase].parseCounts = entries.map((x) => x.parseCount);
    }
  }
}
console.log(JSON.stringify({ url: base, build: 'main data from checkout; generated locally in the runner', runsPerProfile: RUNS, summary, samples: rows }, null, 2));
if (process.env.GITHUB_STEP_SUMMARY) {
  const lines = [
    '# Explore graph setup profile',
    '',
    `Runs: ${RUNS} per profile. Browser cache: fresh context per run; cold opens the Yellowstone food web by hash, warm returns to its place page then reopens Explore in the same context. Service workers are blocked; external map/photo/font requests are blocked; the map uses the app's \`#stub\` style.`,
    '',
    'The inline instrumentation wraps the 120 calls to \`sim.tick()\` in \`loadEco\`, times data preparation, D3 SVG graph construction, pre-tick setup, tick calls, final rendering, and route readiness. Resource Timing response duration and \`Response.json()\` elapsed time (body consumption plus decoding/parsing, not parser-only CPU) are collected separately. These are descriptive measurements, not product changes.',
    '',
    '| Profile / phase | Measure | n | p50 ms | p95 ms | range ms |',
    '|---|---|---:|---:|---:|---:|',
  ];
  for (const [profile, phases] of Object.entries(summary)) for (const [phase, measures] of Object.entries(phases)) {
    for (const [metric, values] of Object.entries(measures)) {
      if (!values || typeof values !== 'object' || !('p50' in values)) continue;
      lines.push(`| ${profile} / ${phase} | ${metric} | ${values.n} | ${values.p50} | ${values.p95} | ${values.min}-${values.max} |`);
    }
    lines.push(`| ${profile} / ${phase} | 120 tick counts | ${measures.tickCounts.length} | ${measures.tickCounts.join(', ')} | - | - |`);
  }
  lines.push('', 'Cold data fetch (ms), JSON parse (ms), transferred bytes:');
  for (const [profile, phases] of Object.entries(summary)) lines.push(`- ${profile}: fetch=${phases.cold.fetchMs.map((x) => x?.toFixed(1) ?? 'missing').join(', ')}; parse=${phases.cold.parseMs.map((x) => x?.toFixed(1) ?? 'missing').join(', ')}; bytes=${phases.cold.transferBytes.join(', ')}`);
  lines.push('', 'Warm request and parse counts:');
  for (const [profile, phases] of Object.entries(summary)) lines.push(`- ${profile}: fetch=${phases.warm.fetchCounts.join(', ')}; parse=${phases.warm.parseCounts.join(', ')}`);
  fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, lines.join('\n') + '\n');
}
