import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

// Owner rule: the app reads everything from data we host. The only outside hosts are the base map tiles.
const SPECIES_PICTURES_FROM_WIKIMEDIA = false;   // our own hosted copies are wired in (#238)
const MAP_HOSTS = /(^|\.)(arcgisonline\.com|openfreemap\.org|amazonaws\.com)$/;
const WIKIMEDIA = /(^|\.)wikimedia\.org$/;
// Request and byte budgets for the first view and for opening a place: counts and sizes do not jitter like timings do, so they can block a change.
// Measured on 2 Nov 2026: 6 requests, 2,691 KB raw (page, 3 fonts, map library, place photo list). Raise one only with a reason written in the pull request.
// 9 since #228 step 2 (was 7): the places are two files instead of being inside the page. 11 since #313 step 3: the local places follow the map in two more files
// (api/places/main/index-local.json and cards-local.json), counted here because the test waits past the photo hold.
const BUDGET = { phone: { startRequests: 11, startKB: 2900 }, desktop: { startRequests: 11, startKB: 2900 } };
const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml' };

describe('the app reads only data we host', () => {
  let browser, srv, base;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      let f = path.join(H.ROOT, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  async function record(size, hash, act) {
    const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
    const own = [], outside = new Set(); let bytes = 0;
    page.on('pageerror', () => {});
    await page.route('**/*', (r) => {
      const u = new URL(r.request().url());
      if (u.hostname === 'localhost' || u.hostname === '127.0.0.1') { own.push(u.pathname); return r.continue(); }
      outside.add(u.hostname);
      return r.abort();
    });
    await page.goto(base + 'index.html' + hash);
    await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(6000);   // past the photo hold, so the whole start is counted
    if (act) await act(page);
    for (const u of new Set(own)) { const f = path.join(H.ROOT, decodeURIComponent(u === '/' ? '/index.html' : u)); if (fs.existsSync(f) && fs.statSync(f).isFile()) bytes += fs.statSync(f).size; }   // sizes of the files served: exact, and the same on every run
    const out = { own, outside: [...outside], kb: Math.round(bytes / 1024) };
    await ctx.close(); return out;
  }
  const bad = (hosts, allowWiki) => hosts.filter((h) => !MAP_HOSTS.test(h) && !(allowWiki && WIKIMEDIA.test(h)));

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: the first view reads no outside host except the map tiles, within its request and size budget`, async () => {
      const r = await record(size, '');
      assert.deepEqual(bad(r.outside, false), [], 'outside hosts at start: ' + r.outside);
      assert.ok(r.own.length <= BUDGET[sizeName].startRequests, `first view made ${r.own.length} requests (budget ${BUDGET[sizeName].startRequests}): ${r.own.join(' ')}`);
      assert.ok(r.kb <= BUDGET[sizeName].startKB, `first view read ${r.kb} KB (budget ${BUDGET[sizeName].startKB})`);
    });

    test(`${sizeName}: opening a place and its food web reads no outside host except the map tiles${SPECIES_PICTURES_FROM_WIKIMEDIA ? ' and the Wikimedia species pictures (until #238)' : ''}`, async () => {
      const r = await record(size, '#e=yellowstone');
      assert.deepEqual(bad(r.outside, SPECIES_PICTURES_FROM_WIKIMEDIA), [], 'outside hosts on a place: ' + r.outside);
    });
  }
});
