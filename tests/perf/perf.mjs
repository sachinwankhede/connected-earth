// perf.mjs: loads the site in Chromium with phone-like and desktop profiles and reports page, map, tap, and route readiness metrics.
// Route metrics include cold/warm place and food-web opens plus selected-species response time.
//   node tests/perf/perf.mjs --url https://... --runs 5 --history perf-data/history.json --out perf-out.json --md perf-out.md
import { chromium } from 'playwright';
import fs from 'node:fs';
import { INITIAL_STAGE_DEFINITIONS, summarizeInitialStages } from './metrics.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const URL_ = arg('url', 'https://sachinwankhede.github.io/connected-earth/');
const RUNS = +arg('runs', 5), OUT = arg('out', 'perf-out.json'), MD = arg('md', 'perf-out.md'), HIST = arg('history', ''), MAP_WAIT = +arg('mapwait', 45000);
const PROFILES = {
  phone: { viewport: { width: 390, height: 800 }, cpu: 4, net: { offline: false, latency: 150, downloadThroughput: (1.6e6) / 8, uploadThroughput: (750e3) / 8 } },
  desktop: { viewport: { width: 1280, height: 800 }, cpu: 1, net: null },
};
const NAV_PLACE = 'yellowstone', NAV_TIMEOUT = 90000;
const RETURNING = arg('returning', '1') !== '0';
const NAV = arg('nav', '1') !== '0';   // --nav 0 skips the route-readiness measurements (used by the A/B comparison, which does not need them)
const median = (a) => { a = a.filter((x) => x != null).sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };
const percentile = (a, p) => {
  a = a.filter((x) => x != null).sort((x, y) => x - y);
  if (!a.length) return null;
  const i = (a.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
  return a[lo] + (a[hi] - a[lo]) * (i - lo);
};

const INIT = () => {
  window.__p = { lt: [], mapLoaded: null, stages: {} };
  const mark = (name, time = performance.now()) => {
    if (window.__p.stages[name] == null) window.__p.stages[name] = time;
  };
  const isVisiblePhoto = (img) => {
    if (!img.matches('#cards img, #speek img') || !img.naturalWidth) return false;
    const r = img.getBoundingClientRect(), s = getComputedStyle(img);
    return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0 &&
      r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight;
  };
  const tileUrl = (url) => /\/MapServer\/tile\/|tiles\.openfreemap\.org\/planet\/\d+\/\d+\/\d+\.pbf(?:$|\?)/i.test(url);
  window.__perfResourceClass = (url) => {
    let u;
    try { u = new URL(url); } catch { return 'other'; }
    if (/\/webs\/[^/]+\.json$/.test(u.pathname)) return 'web data';
    if (/\/data\/[^/]+\.json$/.test(u.pathname)) return 'place data';
    if (/\/photos\//.test(u.pathname) || /wikimedia\.org$/.test(u.hostname)) return 'photos';
    if (/openfreemap|arcgis/.test(u.hostname)) return 'map';
    return 'other';
  };
  try { new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__p.lt.push([e.startTime, e.duration]))).observe({ type: 'longtask', buffered: true }); } catch (e) {}
  try {
    new PerformanceObserver((l) => l.getEntries().forEach((e) => {
      if (tileUrl(e.name)) mark('mapFirstTileResponse', e.responseEnd);
    })).observe({ type: 'resource', buffered: true });
  } catch (e) {}
  document.addEventListener('load', (event) => {
    const img = event.target;
    if (!(img instanceof HTMLImageElement) || !isVisiblePhoto(img)) return;
    mark('firstVisiblePhotoLoad');
    if (img.decode) img.decode().then(() => mark('firstVisiblePhotoDecode')).catch(() => {});
  }, true);
  const iv = setInterval(() => {
    try {
      const m = window.__M;
      if (window.__p.stages.appDataReady == null && m && typeof m.ecoIds === 'function' && m.ecoIds().length) mark('appDataReady');
      if (window.__p.stages.cardsDomRendered == null) {
        const heading = document.querySelector('#cards > li .card h2');
        if (heading && heading.textContent.trim()) mark('cardsDomRendered');
      }
      if (window.__p.stages.mapStyleReady == null && m && m.styleReady) mark('mapStyleReady');
      if (window.__p.stages.photoHoldRelease == null && m && m.photoGo) mark('photoHoldRelease');
      if (window.__p.mapLoaded == null && m && m.map && m.map.loaded && m.map.loaded()) {
        if (!window.__p.mapLoaded) window.__p.mapLoaded = performance.now();
        mark('mapLoaded', window.__p.mapLoaded);
      }
    } catch (e) {}
  }, 20);
  window.__p.stageInterval = iv;
};

async function measuredRoute(page, hash, kind, label) {
  await page.evaluate((h) => {
    performance.clearResourceTimings();
    window.__perfNavStart = performance.now();
    location.hash = h;
  }, hash);
  try {
    await page.waitForFunction((k) => {
      if (k === 'place') {
        const view = document.getElementById('pview');
        return view && !view.hidden && view.querySelector('h2') && view.querySelector('#pgraph .pn');
      }
      const view = document.getElementById('webview'), loading = document.getElementById('webload');
      return view && !view.hidden && loading && loading.hidden && document.querySelector('#svg .node');
    }, kind, { timeout: NAV_TIMEOUT });
  } catch (e) {
    console.error('navigation', label, 'not ready:', e.message);
    return { readyMs: null, resources: {} };
  }
  return page.evaluate(() => {
    const end = performance.now(), start = window.__perfNavStart, resources = {};
    for (const e of performance.getEntriesByType('resource')) {
      if (e.startTime < start || e.startTime > end || e.responseEnd > end) continue;
      const k = window.__perfResourceClass(e.name);
      resources[k] = resources[k] || { requests: 0, kb: 0 };
      resources[k].requests++;
      resources[k].kb += e.transferSize / 1000;
    }
    return { readyMs: end - start, resources };
  });
}

async function measuredSpeciesSelection(page) {
  const started = await page.evaluate(() => {
    const node = document.querySelector('#svg .node');
    if (!node) return false;
    performance.clearResourceTimings();
    window.__perfNavStart = performance.now();
    node.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    return true;
  });
  if (!started) {
    console.error('navigation species selection skipped: no food-web node was available');
    return { readyMs: null, resources: {} };
  }
  try {
    await page.waitForFunction(() => document.querySelector('#svg .node.sel'), null, { timeout: NAV_TIMEOUT });
  } catch (e) {
    console.error('navigation species selection not ready:', e.message);
    return { readyMs: null, resources: {} };
  }
  return page.evaluate(() => {
    const end = performance.now(), start = window.__perfNavStart, resources = {};
    for (const e of performance.getEntriesByType('resource')) {
      if (e.startTime < start || e.startTime > end || e.responseEnd > end) continue;
      const k = window.__perfResourceClass(e.name);
      resources[k] = resources[k] || { requests: 0, kb: 0 };
      resources[k].requests++;
      resources[k].kb += e.transferSize / 1000;
    }
    return { readyMs: end - start, resources };
  });
}

async function navigationScenario(browser, name, kind) {
  const prof = PROFILES[name];
  let ctx;
  const missing = { readyMs: null, resources: {} };
  let firstOpen = missing, repeatOpen = missing, speciesSelection = null, pictures = missing, firstPicture = missing;
  try {
    ctx = await browser.newContext({ viewport: prof.viewport, serviceWorkers: 'block' });
    const p = await ctx.newPage();
    await p.addInitScript(INIT);
    const c = await ctx.newCDPSession(p);
    await c.send('Network.enable');
    if (prof.cpu > 1) await c.send('Emulation.setCPUThrottlingRate', { rate: prof.cpu });
    if (prof.net) await c.send('Network.emulateNetworkConditions', prof.net);
    const base = new URL(URL_); base.hash = '';
    await p.goto(base.toString(), { waitUntil: 'load', timeout: 120000 });
    try { await p.waitForFunction(() => window.__p && window.__p.mapLoaded, null, { timeout: MAP_WAIT }); }
    catch (e) { console.error('navigation baseline map not ready; continuing:', e.message); }
    await p.waitForTimeout(1000);

    const isPlace = kind === 'place', hash = isPlace ? `#pg=${NAV_PLACE}` : `#e=${NAV_PLACE}`;
    firstOpen = await measuredRoute(p, hash, isPlace ? 'place' : 'web', `${kind} cold open`);
    if (isPlace && firstOpen.readyMs != null) {
      // the pictures a place page asks for (food-web preview circles and species cards): when the first and the last one arrived, counted from the tap
      await p.waitForTimeout(8000);
      const pics = await p.evaluate(() => {
        const start = window.__perfNavStart, e = performance.getEntriesByType('resource').filter((x) => x.startTime >= start && /thumb\.wikimedia|upload\.wikimedia|\/photos\//.test(x.name));
        if (!e.length) return null;
        const kb = e.reduce((a, x) => a + x.transferSize, 0) / 1000;
        return { first: Math.min(...e.map((x) => x.responseEnd)) - start, last: Math.max(...e.map((x) => x.responseEnd)) - start, n: e.length, kb };
      });
      if (pics) { firstPicture = { readyMs: pics.first, resources: {} }; pictures = { readyMs: pics.last, resources: { pictures: { requests: pics.n, kb: pics.kb } } }; }
    }
    speciesSelection = isPlace ? null : await measuredSpeciesSelection(p);
    if (!isPlace) {
      await p.evaluate(() => document.getElementById('back').click());
      await p.waitForFunction(() => {
        const view = document.getElementById('pview');
        return view && !view.hidden && view.querySelector('h2') && view.querySelector('#pgraph .pn');
      }, null, { timeout: NAV_TIMEOUT });
    }
    await p.click('#pview [data-pback]');
    await p.waitForFunction(() => { const v = document.getElementById('mapview'); return v && !v.hidden; }, null, { timeout: NAV_TIMEOUT });
    repeatOpen = await measuredRoute(p, hash, isPlace ? 'place' : 'web', `${kind} warm open`);
  } catch (e) {
    console.error('navigation', kind, 'scenario failed:', e.message);
  } finally {
    if (ctx) {
      try { await ctx.close(); } catch (e) { console.error('navigation', kind, 'context close failed:', e.message); }
    }
  }
  return { firstOpen, repeatOpen, ...(kind === 'web' ? { speciesSelection } : { pictures, firstPicture }) };
}

async function navigationMeasurements(browser, name) {
  const place = await navigationScenario(browser, name, 'place');
  const web = await navigationScenario(browser, name, 'web');
  return { place, web };
}

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
    const photoEnd = window.__p.stages.firstVisiblePhotoDecode || window.__p.stages.photoHoldRelease || ml || performance.now();
    const longTasks = window.__p.lt.filter(([s]) => s <= photoEnd);
    if (window.__p.stageInterval) clearInterval(window.__p.stageInterval);
    // what the map asks for, by kind: when the first request started and when the last answer arrived, from the start of the page load
    const mapTl = {};
    const kind = (u) => /server\.arcgisonline\.com/.test(u) ? 'satellite tiles' : /openfreemap\.org\/fonts\//.test(u) ? 'map glyphs' : /openfreemap\.org\/planet\/\d+\/\d+\/\d+\/\d+/.test(u) ? 'vector tiles' : /openfreemap\.org\/(planet|styles)/.test(u) ? 'map style and index' : /amazonaws/.test(u) ? 'terrain tiles' : null;
    for (const e of performance.getEntriesByType('resource')) {
      const k = kind(e.name); if (!k) continue;
      const g = mapTl[k] = mapTl[k] || { n: 0, first: Infinity, last: 0 };
      g.n++; g.first = Math.min(g.first, e.startTime); g.last = Math.max(g.last, e.responseEnd);
    }
    return {
      mapTl,
      fcp: f && f.startTime, dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd, mapLoaded: ml, tbtToMap: tbt, longTasks: window.__p.lt.length,
      initialStages: {
        domInteractive: n.domInteractive,
        domContentLoaded: n.domContentLoadedEventEnd,
        load: n.loadEventEnd,
        firstContentfulPaint: f && f.startTime,
        ...window.__p.stages,
      },
      initialLongTasks: {
        count: longTasks.length,
        durationMs: longTasks.reduce((a, [, d]) => a + d, 0),
        blockingMs: longTasks.reduce((a, [, d]) => a + Math.max(0, d - 50), 0),
      },
    };
  });
  Object.assign(r, m);
  r.kbTotal = Object.values(bytes).reduce((a, b) => a + b.kb, 0);
  r.requests = Object.values(bytes).reduce((a, b) => a + b.n, 0);
  r.wikipediaRequests = (bytes['en.wikipedia.org'] || { n: 0 }).n;
  r.hosts = bytes;
  r.initialStages = m.initialStages;
  r.initialLongTasks = m.initialLongTasks;
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

// Returning visit: the first visit installs the service worker and fills its caches; the second visit (a new page in the same browser context)
// is what a person who opens the app again sees. Observational only. Playwright's CDP throttling is attached to the page, so requests made by the
// service worker itself may not be slowed; the document request is therefore also recorded (status, served by the worker or not, bytes on the wire),
// so the report shows whether the page was re-downloaded or only re-checked.
async function returningVisit(browser, name) {
  const prof = PROFILES[name];
  const ctx = await browser.newContext({ viewport: prof.viewport });
  const origin = new URL(URL_).origin;
  let docs = [];
  ctx.on('response', async (res) => {
    try {
      const rq = res.request();
      const u = new URL(rq.url());
      if (u.origin !== origin || !(rq.resourceType() === 'document' || u.pathname.endsWith('/') || u.pathname.endsWith('.html'))) return;
      const sz = await rq.sizes();
      let sw = false;
      try { sw = !!rq.serviceWorker(); } catch (e) {}
      docs.push({ sw, status: res.status(), fromSW: res.fromServiceWorker(), bodyBytes: sz.responseBodySize >= 0 ? sz.responseBodySize : null });
    } catch (e) {}
  });
  const throttle = async (p) => {
    const c = await ctx.newCDPSession(p);
    await c.send('Network.enable');
    if (prof.cpu > 1) await c.send('Emulation.setCPUThrottlingRate', { rate: prof.cpu });
    if (prof.net) await c.send('Network.emulateNetworkConditions', prof.net);
  };
  const first = await ctx.newPage();
  await throttle(first);
  await first.goto(URL_, { waitUntil: 'load', timeout: 120000 });
  const swReady = await first.evaluate(() => (navigator.serviceWorker ? Promise.race([navigator.serviceWorker.ready.then(() => true), new Promise((r) => setTimeout(() => r(false), 20000))]) : false));
  await first.waitForTimeout(4000);
  await first.close();
  docs = [];
  const p = await ctx.newPage();
  await p.addInitScript(INIT);
  await throttle(p);
  await p.goto(URL_, { waitUntil: 'load', timeout: 120000 });
  try { await p.waitForFunction(() => window.__p && window.__p.mapLoaded, null, { timeout: MAP_WAIT }); } catch (e) {}
  await p.waitForTimeout(1500);
  const m = await p.evaluate(() => {
    const n = performance.getEntriesByType('navigation')[0], f = performance.getEntriesByName('first-contentful-paint')[0];
    const ml = window.__p.mapLoaded;
    return {
      fcp: f && f.startTime, domInteractive: n.domInteractive, load: n.loadEventEnd, mapLoaded: ml,
      blockingMs: window.__p.lt.filter(([s]) => ml == null || s < ml).reduce((a, [, d]) => a + Math.max(0, d - 50), 0),
      controlled: !!(navigator.serviceWorker && navigator.serviceWorker.controller),
    };
  });
  // the page's own document response (possibly answered by the worker) and the worker's own network fetch of the document, if any
  const pageDoc = docs.find((d) => !d.sw) || null, swDoc = docs.find((d) => d.sw) || null;
  await ctx.close();
  return {
    ...m, swReady,
    docStatus: pageDoc && pageDoc.status, docFromSW: pageDoc && pageDoc.fromSW,
    swFetchStatus: swDoc && swDoc.status, swFetchBytes: swDoc && swDoc.bodyBytes,
  };
}

const MAP_KINDS = ['map style and index', 'vector tiles', 'map glyphs', 'satellite tiles', 'terrain tiles'];
const FLAT = {
  ...Object.fromEntries(MAP_KINDS.flatMap((k) => [[`map: ${k}, first request (ms)`, (r) => r.mapTl && r.mapTl[k] && r.mapTl[k].first], [`map: ${k}, last answer (ms)`, (r) => r.mapTl && r.mapTl[k] && r.mapTl[k].last], [`map: ${k}, requests`, (r) => r.mapTl && r.mapTl[k] && r.mapTl[k].n]])),
  'first paint (ms)': (r) => r.fcp, 'page loaded (ms)': (r) => r.load, 'map drawn (ms)': (r) => r.mapLoaded, 'blocked before map (ms)': (r) => r.tbtToMap,
  'download (KB)': (r) => r.kbTotal, 'requests': (r) => r.requests, 'Wikipedia requests': (r) => r.wikipediaRequests,
};
function summarize(runs) {
  const s = {};
  for (const [k, f] of Object.entries(FLAT)) s[k] = median(runs.map(f));
  const names = runs.length ? Object.keys(runs[0].taps) : [];
  for (const n of names) { s['tap: ' + n + ' (ms)'] = median(runs.map((r) => r.taps[n] && r.taps[n].ms)); s['tap: ' + n + ' blocked (ms)'] = median(runs.map((r) => r.taps[n] && r.taps[n].blocked)); }
  const h = {}; for (const r of runs) for (const [k, v] of Object.entries(r.hosts)) { h[k] = h[k] || []; h[k].push(v); }
  s.hosts = Object.fromEntries(Object.entries(h).map(([k, v]) => [k, { requests: median(v.map((x) => x.n)), kb: Math.round(median(v.map((x) => x.kb))) }]));
  const navPhases = {
    'place cold open': (r) => r.navigation.place.firstOpen,
    'place warm open': (r) => r.navigation.place.repeatOpen,
    'place first picture arrived': (r) => r.navigation.place.firstPicture,
    'place last picture arrived': (r) => r.navigation.place.pictures,
    'food-web cold open': (r) => r.navigation.web.firstOpen,
    'food-web warm open': (r) => r.navigation.web.repeatOpen,
    'species selection': (r) => r.navigation.web.speciesSelection,
  };
  s.navigation = {};
  s.navigationResources = {};
  for (const [phase, get] of Object.entries(navPhases)) {
    const samples = runs.map((r) => get(r)).filter(Boolean);
    const times = samples.map((x) => x.readyMs);
    s.navigation[phase] = { n: times.filter((x) => x != null).length, p50: percentile(times, 0.5), p95: percentile(times, 0.95) };
    const successful = samples.filter((x) => x.readyMs != null);
    const classes = new Set(successful.flatMap((x) => Object.keys(x.resources)));
    s.navigationResources[phase] = Object.fromEntries([...classes].map((k) => {
      const values = successful.map((x) => x.resources[k] || { requests: 0, kb: 0 });
      return [k, { requests: median(values.map((x) => x.requests)), kb: Math.round(median(values.map((x) => x.kb))) }];
    }));
  }
  s.initialLoad = summarizeInitialStages(runs, RUNS);
  const rv = runs.map((r) => r.returning).filter(Boolean);
  const col = (k) => rv.map((x) => x[k]).filter(Number.isFinite);
  const count = (f) => rv.filter(f).length;
  s.returning = {
    samples: rv.length,
    controlled: count((x) => x.controlled),
    swReady: count((x) => x.swReady),
    metrics: Object.fromEntries(['fcp', 'domInteractive', 'load', 'mapLoaded', 'blockingMs'].map((k) => [k, { p50: percentile(col(k), 0.5), p95: percentile(col(k), 0.95) }])),
    docStatuses: Object.fromEntries([...new Set(rv.map((x) => x.docStatus))].map((st) => [String(st), count((x) => x.docStatus === st)])),
    docFromSW: count((x) => x.docFromSW),
    swFetchStatuses: Object.fromEntries([...new Set(rv.map((x) => x.swFetchStatus))].map((st) => [String(st), count((x) => x.swFetchStatus === st)])),
    swFetchBytesP50: percentile(col('swFetchBytes'), 0.5),
    // the worker asks the server to re-check the page; a 304 reaches Playwright as a 200 with an empty body, so an empty body means re-checked only
    // (observed on the live site: about 150 bytes, which is far too small to be the page, so the cut-off is 10 KB rather than zero)
    swRechecked: count((x) => x.swFetchStatus === 304 || (x.swFetchBytes != null && x.swFetchBytes < 10000)),
    swDownloaded: count((x) => x.swFetchBytes != null && x.swFetchBytes >= 10000),
  };
  return s;
}

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: process.env.CHROMIUM_PATH ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox'] : [],
});
const result = { when: new Date().toISOString(), url: URL_, runs: RUNS, sha: process.env.GITHUB_SHA || '' };
for (const name of Object.keys(PROFILES)) {
  const rs = [];
  for (let i = 0; i < RUNS; i++) {
    try {
      const run = await oneRun(browser, name);
      run.navigation = NAV ? await navigationMeasurements(browser, name) : { place: {}, web: {} };
      if (RETURNING) {
        try { run.returning = await returningVisit(browser, name); } catch (e) { console.error(name, 'run', i, 'returning visit failed:', e.message); }
      }
      rs.push(run);
    } catch (e) { console.error(name, 'run', i, 'failed:', e.message); }
  }
  result[name] = summarize(rs);
}
await browser.close();
fs.writeFileSync(OUT, JSON.stringify(result, null, 1));

// report, compared with the last entry of the history
let prev = null;
try { const h = JSON.parse(fs.readFileSync(HIST, 'utf8')); prev = h[h.length - 1]; } catch (e) {}
const fmt = (v) => (v == null ? 'n/a' : Math.round(v).toString());
let md = `# Site speed, ${result.when.slice(0, 16).replace('T', ' ')} UTC\n\n${URL_}  \nMedian of ${RUNS} runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.\n`;
for (const name of Object.keys(PROFILES)) {
  const s = result[name];
  md += `\n## ${name}\n\n| Metric | Now | Previous | Change |\n|---|---|---|---|\n`;
  for (const [k, v] of Object.entries(s)) {
    if (k === 'hosts' || k === 'navigation' || k === 'navigationResources' || k === 'initialLoad' || k === 'returning') continue;
    const pv = prev && prev[name] && prev[name][k]; const d = v != null && pv ? (v - pv) / pv : null;
    const lowerIsBetter = true; const flag = d != null && d > 0.15 && v - pv > 20 ? ' ⚠' : '';
    md += `| ${k} | ${fmt(v)} | ${fmt(pv)} | ${d == null ? '' : (d > 0 ? '+' : '') + Math.round(d * 100) + '%'}${flag} |\n`;
  }
  md += `\nBy host: ` + Object.entries(s.hosts).sort((a, b) => b[1].kb - a[1].kb).slice(0, 8).map(([h, x]) => `${h} ${x.requests} req / ${x.kb} KB`).join('; ') + '\n';
  md += `\n### Initial Places-page load stages (observational)\n\n`;
  md += `Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.\n\n`;
  md += `Requested runs: ${s.initialLoad.attemptedRuns}; completed: ${s.initialLoad.completedRuns}; failed: ${s.initialLoad.failedRuns}.\n\n`;
  md += `| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |\n|---|---:|---:|---:|---:|---|\n`;
  for (const [phase, v] of Object.entries(s.initialLoad.phases)) {
    const label = INITIAL_STAGE_DEFINITIONS[phase].label;
    md += `| ${label} | ${v.samples} | ${v.failures} | ${fmt(v.p50)} | ${fmt(v.p95)} | ${v.method} |\n`;
  }
  const lt = s.initialLoad.longTasks;
  if (!s.initialLoad.completedRuns) md += `No run finished.\n\n`;
  md += `\nLong tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): ${lt.samples} samples, ${lt.failures} failures. Count p50/p95 ${fmt(lt.count.p50)}/${fmt(lt.count.p95)}; total duration ${fmt(lt.durationMs.p50)}/${fmt(lt.durationMs.p95)} ms; blocking time over 50 ms ${fmt(lt.blockingMs.p50)}/${fmt(lt.blockingMs.p95)} ms.\n`;
  if (RETURNING) {
    const rt = s.returning;
    md += `\n### Returning visit, service worker on (observational)\n\n`;
    md += `A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.\n\n`;
    md += `Samples: ${rt.samples}; service worker ready: ${rt.swReady}; page controlled by the worker on the second visit: ${rt.controlled}. Page document: status ${Object.entries(rt.docStatuses).map(([st, n]) => `${st} x${n}`).join(', ') || 'n/a'}; answered by the worker: ${rt.docFromSW}. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): ${rt.swRechecked}; downloaded again (10 KB or more): ${rt.swDownloaded}; status ${Object.entries(rt.swFetchStatuses).map(([st, n]) => `${st} x${n}`).join(', ') || 'n/a'}; body bytes (p50): ${fmt(rt.swFetchBytesP50)}. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.\n\n`;
    md += `| Metric | p50 (ms) | p95 (ms) |\n|---|---:|---:|\n`;
    for (const [k, label] of [['fcp', 'First contentful paint'], ['domInteractive', 'DOM interactive'], ['load', 'Load event'], ['mapLoaded', 'Map loaded'], ['blockingMs', 'Blocking time before map loaded']]) md += `| ${label} | ${fmt(rt.metrics[k].p50)} | ${fmt(rt.metrics[k].p95)} |\n`;
  }
  md += `\n### Navigation readiness (observational)\n\n`;
  md += `Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.\n\n`;
  md += `| Route phase | Ready samples | p50 (ms) | p95 (ms) |\n|---|---:|---:|---:|\n`;
  for (const [phase, v] of Object.entries(s.navigation)) md += `| ${phase} | ${v.n} | ${fmt(v.p50)} | ${fmt(v.p95)} |\n`;
  md += `\nMedian resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):\n\n| Route phase | Resource class | Requests | KB |\n|---|---|---:|---:|\n`;
  for (const [phase, classes] of Object.entries(s.navigationResources)) {
    if (!Object.keys(classes).length) md += `| ${phase} | none recorded | 0 | 0 |\n`;
    else for (const [resource, v] of Object.entries(classes)) md += `| ${phase} | ${resource} | ${fmt(v.requests)} | ${fmt(v.kb)} |\n`;
  }
}
fs.writeFileSync(MD, md);
console.log(md);
