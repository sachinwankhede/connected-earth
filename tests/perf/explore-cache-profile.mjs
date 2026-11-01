import { chromium } from 'playwright';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const MAIN = path.join(ROOT, 'index.html');
const arg = (key, fallback) => {
  const index = process.argv.indexOf('--' + key);
  return index > 0 ? process.argv[index + 1] : fallback;
};
const runs = Number(arg('runs', 5));
const profiles = {
  phone: { viewport: { width: 390, height: 800 }, cpu: 4, network: { offline: false, latency: 150, downloadThroughput: 200000, uploadThroughput: 93750 } },
  desktop: { viewport: { width: 1280, height: 800 }, cpu: 1, network: null },
};
const percentile = (values, p) => {
  const sorted = values.slice().sort((a, b) => a - b);
  const index = (sorted.length - 1) * p;
  const low = Math.floor(index), high = Math.ceil(index);
  return sorted[low] + (sorted[high] - sorted[low]) * (index - low);
};
const summarize = (samples, field) => ({
  p50: percentile(samples.map((sample) => sample[field]), 0.5),
  p95: percentile(samples.map((sample) => sample[field]), 0.95),
});
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
const server = http.createServer((request, response) => {
  const file = path.resolve(ROOT, '.' + decodeURIComponent(new URL(request.url, 'http://localhost').pathname));
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    response.statusCode = 404;
    response.end();
    return;
  }
  response.setHeader('content-type', mime[path.extname(file)] || 'application/octet-stream');
  response.end(fs.readFileSync(file));
});

async function openAndMeasure(page) {
  const start = await page.evaluate(() => {
    performance.clearResourceTimings();
    window.__M.layoutInfo = null;
    window.__routeStart = performance.now();
    location.hash = '#stub&e=yellowstone';
    return window.__routeStart;
  });
  await page.waitForFunction(() => window.__M && window.__M.layoutInfo && document.querySelector('#svg .node'), null, { timeout: 60000 });
  return page.evaluate((routeStart) => {
    const data = window.__M.layoutInfo;
    const resources = performance.getEntriesByType('resource').filter((entry) => /\/webs\/yellowstone\.json(?:$|\?)/.test(entry.name));
    return {
      routeReadyMs: performance.now() - routeStart,
      setupMs: data.setupMs,
      buildMs: data.buildMs,
      tickMs: data.tickMs,
      ticks: data.ticks,
      cacheHit: data.cacheHit,
      webRequests: resources.length,
      webBytes: resources.reduce((sum, entry) => sum + (entry.transferSize || 0), 0),
    };
  }, start);
}

async function sample(browser, profile) {
  const context = await browser.newContext({ viewport: profile.viewport, serviceWorkers: 'block' });
  try {
    const page = await context.newPage();
    await page.addInitScript(() => { window.__CE_LAYOUT_PROFILE__ = true; });
    await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (route) => route.abort());
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    if (profile.cpu > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: profile.cpu });
    if (profile.network) await cdp.send('Network.emulateNetworkConditions', profile.network);
    await page.goto(`http://127.0.0.1:${server.address().port}/index.html#stub`, { waitUntil: 'load', timeout: 90000 });
    await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 90000 });
    await page.waitForTimeout(500);
    const cold = await openAndMeasure(page);
    if (cold.cacheHit || cold.ticks !== 120) throw new Error('Expected cold graph setup to run all 120 ticks: ' + JSON.stringify(cold));

    await page.evaluate(() => document.getElementById('back').click());
    await page.waitForFunction(() => {
      const view = document.getElementById('pview');
      return view && !view.hidden && view.querySelector('#pgraph .pn');
    }, null, { timeout: 60000 });
    await page.click('#pview [data-pback]');
    await page.waitForFunction(() => !document.getElementById('mapview').hidden, null, { timeout: 60000 });
    const warm = await openAndMeasure(page);
    if (!warm.cacheHit || warm.ticks !== 0) throw new Error('Expected warm graph setup to reuse its layout: ' + JSON.stringify(warm));
    return { cold, warm };
  } finally {
    await context.close();
  }
}

await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', resolve);
});
let browser;
try {
  browser = await chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const report = {};
  for (const [name, profile] of Object.entries(profiles)) {
    report[name] = { samples: [] };
    for (let run = 0; run < runs; run++) report[name].samples.push(await sample(browser, profile));
    for (const phase of ['cold', 'warm']) {
      report[name][phase] = {};
      for (const field of ['routeReadyMs', 'setupMs', 'buildMs', 'tickMs']) {
        report[name][phase][field] = summarize(report[name].samples.map((sample) => sample[phase]), field);
      }
    }
  }
  console.log(JSON.stringify(report, null, 2));
  console.log('\n| Profile | Phase | Route ready p50/p95 | Setup p50/p95 | SVG build p50/p95 | Tick time p50/p95 | Samples |');
  console.log('|---|---|---:|---:|---:|---:|---:|');
  for (const name of Object.keys(profiles)) for (const phase of ['cold', 'warm']) {
    const metrics = report[name][phase];
    const fmt = (field) => `${metrics[field].p50.toFixed(1)} / ${metrics[field].p95.toFixed(1)} ms`;
    console.log(`| ${name} | ${phase} | ${fmt('routeReadyMs')} | ${fmt('setupMs')} | ${fmt('buildMs')} | ${fmt('tickMs')} | ${runs} |`);
  }
  console.log('\nEach cold sample used a fresh browser context; each warm sample reopened Yellowstone in that context. Phone: 390x800, 4x CPU, 150 ms latency, 1.6 Mbps download. Desktop: 1280x800, unthrottled. Service workers and external map/photo/font hosts were blocked; web data was served from the Actions runner. p95 uses linear interpolation over the sample set.');
} finally {
  if (browser) await browser.close();
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}
