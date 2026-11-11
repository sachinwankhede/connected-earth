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
// 9 since #228 step 2 (was 7): the places are two files instead of being inside the page. (11 from #313 step 3 to 3 Nov: the local places followed the map in two more files; they now load only when something needs them: the local button, a search, Near me or a link to a local place.)
const BUDGET = { phone: { startRequests: 9, startKB: 2900, placeRequests: 56, placeKB: 3200 }, desktop: { startRequests: 9, startKB: 2900, placeRequests: 56, placeKB: 3200 } };
// Opening a place by link and its food web (#562), measured 11 Nov 2026 on phone and desktop alike: 48 requests, 2,977 KB raw (page, 3 fonts, map library, 4 place files,
//  2 shared lists, 36 photos, 1 other). placeRequests 56 and placeKB 3200 leave room for the photo count and for data growth; the failure message lists the requests by kind.
// What each number allows (#292), so a failure says what to look at before anyone raises it:
//  startRequests: the requests to our own site before the person touches anything, nothing counted for the map tiles (another host). That is the page, its fonts,
//    the map library, the two world-place files (index and cards), the place photo list and the species picture list. A new kind of request here is a new cost on every first open.
//  startKB: the raw bytes of those same files (sizes of the files served, exact, the same on every run). The page and the map library are most of it. The gzip bytes the phone
//    actually carries are limited separately, in build/firstview.py (#369).
// Raise a number only with the reason in the pull request, and update this note.
const kind = (u) => /\.woff2$/.test(u) ? 'font' : /maplibre-gl/.test(u) ? 'map library' : /\/api\/places\//.test(u) ? 'place files' : /\/api\//.test(u) ? 'shared lists' : /\/photos\//.test(u) ? 'photos' : /\.html$|\/$/.test(u) ? 'page' : 'other';
const byKind = (own) => { const c = {}; for (const u of new Set(own)) c[kind(u)] = (c[kind(u)] || 0) + 1; return Object.entries(c).map(([k, n]) => `${k} ${n}`).join(', '); };
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
      assert.ok(r.own.length <= BUDGET[sizeName].startRequests, `first view made ${r.own.length} requests (budget ${BUDGET[sizeName].startRequests}; by kind: ${byKind(r.own)}): ${r.own.join(' ')}`);
      assert.ok(r.kb <= BUDGET[sizeName].startKB, `first view read ${r.kb} KB (budget ${BUDGET[sizeName].startKB})`);
    });

    test(`${sizeName}: opening a place and its food web reads no outside host except the map tiles${SPECIES_PICTURES_FROM_WIKIMEDIA ? ' and the Wikimedia species pictures (until #238)' : ''}`, async () => {
      const r = await record(size, '#e=yellowstone');
      assert.deepEqual(bad(r.outside, SPECIES_PICTURES_FROM_WIKIMEDIA), [], 'outside hosts on a place: ' + r.outside);
      // the request and size budget for opening a place by link and its food web (#562): our own files only, counted from a fresh load, sizes of the files served
      assert.ok(r.own.length <= BUDGET[sizeName].placeRequests, `opening a place made ${r.own.length} requests (budget ${BUDGET[sizeName].placeRequests}; by kind: ${byKind(r.own)}): ${r.own.join(' ')}`);
      assert.ok(r.kb <= BUDGET[sizeName].placeKB, `opening a place read ${r.kb} KB (budget ${BUDGET[sizeName].placeKB})`);
    });
  }
});
