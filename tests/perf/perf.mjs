// perf.mjs: loads the site in a real Chromium with a phone-like and a desktop profile, times the page load and the main taps,
// and prints a markdown report compared with the previous run. Never fails the build: it only reports.
//   node tests/perf/perf.mjs --url https://... --runs 5 --history perf-data/history.json --out perf-out.json --md perf-out.md
import { chromium } from 'playwright';
import fs from 'node:fs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const URL_ = arg('url', 'https://sachinwankhede.github.io/connected-earth/');
const RUNS = +arg('runs', 5), OUT = arg('out', 'perf-out.json'), MD = arg('md', 'perf-out.md'), HIST = arg('history', ''), MAP_WAIT = +arg('mapwait', 45000);
const PROFILES = {
  phone: { viewport: { width: 390, height: 800 }, cpu: 4, net: { offline: false, latency: 150, downloadThroughput: (1.6e6) / 8, uploadThroughput: (750e3) / 8 } },
  desktop: { viewport: { width: 1280, height: 800 }, cpu: 1, net: null },
};
const median = (a) => { a = a.filter((x) => x != null).sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };

const INIT = () => {
  window.__p = { lt: [], mapLoaded: null };
  try { new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__p.lt.push([e.startTime, e.duration]))).observe({ type: 'longtask', buffered: true }); } catch (e) {}
  const iv = setInterval(() => { try { if (window.__M && __M.map && __M.map.loaded && __M.map.loaded() && !window.__p.mapLoaded) { window.__p.mapLoaded = performance.now(); clearInterval(iv); } } catch (e) {} }, 40);
};

// one tap: click an element in the page, wait for the second frame after it, and add up the long tasks in the next second
async function tap(p, sel, opts = {}) {
  return p.evaluate(async ([sel, opts]) => {
    const vis = [...document.querySelectorAll(sel)].find((e) => e.offsetParent !== null || e.getClientRects().length);
    if (!vis) return null;
    const t0 = performance.now();
    vis.click();
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    const t1 = performance.now();
    await new Promise((r) => setTimeout(r, opts.settle || 900));
    const blocked = window.__p.lt.filter(([s]) => s >= t0 && s < t0 + 1000).reduce((a, [, d]) => a + Math.max(0, d - 50), 0);
    return { ms: Math.round(t1 - t0), blocked: Math.round(blocked) };
  }, [sel, opts]);
}

async function oneRun(browser, name) {
  const prof = PROFILES[name];
  const ctx = await browser.newContext({ viewport: prof.viewport, serviceWorkers: 'block' });
  const p = await ctx.newPage();
  await p.addInitScript(INIT);
  const c = await ctx.newCDPSession(p);
  await c.send('Network.enable');
  if (prof.cpu > 1) await c.send('Emulation.setCPUThrottlingRate', { rate: prof.cpu });
  if (prof.net) await c.send('Network.emulateNetworkConditions', prof.net);
  const urls = {}, bytes = {};
  c.on('Network.requestWillBeSent', (e) => { urls[e.requestId] = e.request.url; });
  c.on('Network.loadingFinished', (e) => { const u = urls[e.requestId]; if (!u) return; let h; try { h = new URL(u).host; } catch { return; } bytes[h] = bytes[h] || { n: 0, kb: 0 }; bytes[h].n++; bytes[h].kb += e.encodedDataLength / 1000; });
  const r = {};
  await p.goto(URL_, { waitUntil: 'load', timeout: 120000 });
  try { await p.waitForFunction(() => window.__p && window.__p.mapLoaded, null, { timeout: MAP_WAIT }); } catch (e) {}
  await p.waitForTimeout(2500);
  const m = await p.evaluate(() => {
    const n = performance.getEntriesByType('navigation')[0], f = performance.getEntriesByName('first-contentful-paint')[0];
    const ml = window.__p.mapLoaded;
    const tbt = window.__p.lt.filter(([s]) => ml == null || s < ml).reduce((a, [, d]) => a + Math.max(0, d - 50), 0);
    return { fcp: f && f.startTime, dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd, mapLoaded: ml, tbtToMap: tbt, longTasks: window.__p.lt.length };
  });
  Object.assign(r, m);
  r.kbTotal = Object.values(bytes).reduce((a, b) => a + b.kb, 0);
  r.requests = Object.values(bytes).reduce((a, b) => a + b.n, 0);
  r.wikipediaRequests = (bytes['en.wikipedia.org'] || { n: 0 }).n;
  r.hosts = bytes;
  // taps
  const T = {};
  const put = (k, v) => { T[k] = v; };
  put('filter on', await tap(p, '#kinds .chip'));
  put('filter off', await tap(p, '#kinds .chip.on'));
  put('state parks on', await tap(p, '#locbtn'));
  put('state parks off', await tap(p, '#locbtn'));
  // fresh page for the place and journey taps, so earlier filters do not change what is on screen
  await p.goto(URL_, { waitUntil: 'load', timeout: 120000 });
  await p.waitForTimeout(3000);
  if (name === 'phone') await tap(p, '#speek');
  put('open place', await tap(p, '#cards [data-eco]', { settle: 1500 }));
  put('back from place', await tap(p, '[data-pback]', { settle: 1200 }));
  put('journeys tab', await tap(p, '[data-tab="journeys"]'));
  put('open journey', await tap(p, '#xcards li:not([hidden]) .jcard', { settle: 1500 }));
  put('back from journey', await tap(p, '[data-jback]', { settle: 1200 }));
  r.taps = T;
  await ctx.close();
  return r;
}

const FLAT = {
  'first paint (ms)': (r) => r.fcp, 'page loaded (ms)': (r) => r.load, 'map drawn (ms)': (r) => r.mapLoaded, 'blocked before map (ms)': (r) => r.tbtToMap,
  'download (KB)': (r) => r.kbTotal, 'requests': (r) => r.requests, 'Wikipedia requests': (r) => r.wikipediaRequests,
};
function summarize(runs) {
  const s = {};
  for (const [k, f] of Object.entries(FLAT)) s[k] = median(runs.map(f));
  const names = Object.keys(runs[0].taps);
  for (const n of names) { s['tap: ' + n + ' (ms)'] = median(runs.map((r) => r.taps[n] && r.taps[n].ms)); s['tap: ' + n + ' blocked (ms)'] = median(runs.map((r) => r.taps[n] && r.taps[n].blocked)); }
  const h = {}; for (const r of runs) for (const [k, v] of Object.entries(r.hosts)) { h[k] = h[k] || []; h[k].push(v); }
  s.hosts = Object.fromEntries(Object.entries(h).map(([k, v]) => [k, { requests: median(v.map((x) => x.n)), kb: Math.round(median(v.map((x) => x.kb))) }]));
  return s;
}

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const result = { when: new Date().toISOString(), url: URL_, runs: RUNS, sha: process.env.GITHUB_SHA || '' };
for (const name of Object.keys(PROFILES)) {
  const rs = [];
  for (let i = 0; i < RUNS; i++) { try { rs.push(await oneRun(browser, name)); } catch (e) { console.error(name, 'run', i, 'failed:', e.message); } }
  result[name] = rs.length ? summarize(rs) : null;
}
await browser.close();
fs.writeFileSync(OUT, JSON.stringify(result, null, 1));

// report, compared with the last entry of the history
let prev = null;
try { const h = JSON.parse(fs.readFileSync(HIST, 'utf8')); prev = h[h.length - 1]; } catch (e) {}
const fmt = (v) => (v == null ? 'n/a' : Math.round(v).toString());
let md = `# Site speed, ${result.when.slice(0, 16).replace('T', ' ')} UTC\n\n${URL_}  \nMedian of ${RUNS} runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Both load from a GitHub runner over the real internet. A mark ⚠ means more than 15% worse than the previous run.\n`;
for (const name of Object.keys(PROFILES)) {
  const s = result[name]; if (!s) { md += `\n## ${name}\n\nNo run finished.\n`; continue; }
  md += `\n## ${name}\n\n| Metric | Now | Previous | Change |\n|---|---|---|---|\n`;
  for (const [k, v] of Object.entries(s)) {
    if (k === 'hosts') continue;
    const pv = prev && prev[name] && prev[name][k]; const d = v != null && pv ? (v - pv) / pv : null;
    const lowerIsBetter = true; const flag = d != null && d > 0.15 && v - pv > 20 ? ' ⚠' : '';
    md += `| ${k} | ${fmt(v)} | ${fmt(pv)} | ${d == null ? '' : (d > 0 ? '+' : '') + Math.round(d * 100) + '%'}${flag} |\n`;
  }
  md += `\nBy host: ` + Object.entries(s.hosts).sort((a, b) => b[1].kb - a[1].kb).slice(0, 8).map(([h, x]) => `${h} ${x.requests} req / ${x.kb} KB`).join('; ') + '\n';
}
fs.writeFileSync(MD, md);
console.log(md);
