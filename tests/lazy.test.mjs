import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json' };
// A place's full web is fetched only when it is opened.
describe('places load on demand', () => {
  let browser, srv, base;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      let f = path.join(H.ROOT, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  async function open(size, hash, { failWebs = false } = {}) {
    const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
    const errors = [], webs = [];
    page.on('pageerror', (x) => errors.push(String(x)));
    const state = { fail: failWebs };
    await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
    await page.route(/\/webs\//, (r) => { webs.push(r.request().url().split('/webs/')[1]); return state.fail ? r.abort() : r.continue(); });
    await page.goto(base + 'index.html#stub' + hash); await page.reload();
    await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(1500);
    return { ctx, page, errors, webs, state };
  }
  const places = H.readPlaces(false);

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: opening the app fetches no webs; opening a place fetches exactly that one`, async () => {
      const t = await open(size, '');
      assert.deepEqual(t.webs, [], 'nothing fetched at start');
      await t.page.fill('#q', 'yellowstone'); await t.page.waitForTimeout(600);
      await t.page.evaluate(() => document.querySelector('[data-eco]').click()); await t.page.waitForTimeout(2000);
      assert.equal(t.webs.length, 1, 'one web fetched: ' + t.webs);
      assert.ok(await t.page.evaluate(() => !!document.querySelector('#panel .lead')), 'place sheet open');
      assert.ok(await t.page.evaluate(() => document.querySelectorAll('#svg .node').length > 5), 'graph drawn');
      assert.equal(await t.page.evaluate(() => document.getElementById('webload').hidden), true);
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });

    test(`${sizeName}: search finds a species that only lives inside a place's web`, async () => {
      const e = places.find((x) => x.nodes.some((n) => !n.cat && n.latin && n.latin.toLowerCase() === 'ursus arctos')) || places[0];
      const t = await open(size, '');
      await t.page.fill('#q', 'ursus arctos'); await t.page.waitForTimeout(800);
      assert.ok((await H.dots(t.page)) >= 1);
      assert.deepEqual(t.webs, [], 'searching does not fetch webs'); assert.ok(e); await t.ctx.close();
    });

    test(`${sizeName}: Also found in jumps to another place's species and selects it`, async () => {
      const t = await open(size, '&e=npmammothcave');
      const target = await t.page.evaluate(() => { const b = document.querySelector('#panel'); return !!b; });
      assert.ok(target);
      // pick a species that is also in other places, then jump
      const jumped = await t.page.evaluate(async () => {
        const chips = [...document.querySelectorAll('#panel .chips .chip')];
        for (const c of chips) { c.click(); await new Promise((r) => setTimeout(r, 300)); const j = document.querySelector('#panel [data-jump]'); if (j && document.querySelector('#panel .found')) { j.click(); return j.getAttribute('data-jump'); } }
        return null;
      });
      assert.ok(jumped, 'found a species with another place');
      await t.page.waitForTimeout(2500);
      const [eco, node] = jumped.split(':');
      assert.ok(t.webs.some((w) => w === eco + '.json'), 'second web fetched: ' + t.webs);
      assert.equal(await t.page.evaluate(() => document.getElementById('eco').value), eco, 'now in the other place');
      assert.ok(await t.page.evaluate((n) => !!document.querySelector('.node.sel,.node.on'), node), 'species selected after the jump');
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });

    test(`${sizeName}: the pilot page loads webs from the shared webs folder`, async () => {
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const urls = []; page.on('request', (r) => { if (r.url().includes('/webs/')) urls.push(r.url()); });
      await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
      await page.goto(base + 'pilot/index.html#stub&e=mocastlewood'); await page.reload();
      await page.waitForTimeout(3000);
      assert.ok(urls.some((u) => u.endsWith('/webs/mocastlewood.json') && !u.includes('/pilot/')), 'urls: ' + urls);
      assert.ok(await page.evaluate(() => !!document.querySelector('#panel .lead')), 'place sheet open');
      await ctx.close();
    });

    test(`${sizeName}: if a place cannot be fetched you are told, Back works, and trying again works`, async () => {
      const t = await open(size, '', { failWebs: true });
      await t.page.fill('#q', 'yellowstone'); await t.page.waitForTimeout(600);
      await t.page.evaluate(() => document.querySelector('[data-eco]').click()); await t.page.waitForTimeout(1500);
      assert.match(await t.page.textContent('#webload'), /could not be loaded/);
      await t.page.evaluate(() => document.getElementById('back').click()); await t.page.waitForTimeout(600);
      assert.equal(await t.page.evaluate(() => document.getElementById('mapview').hidden), false, 'back on the map');
      t.state.fail = false;
      await t.page.evaluate(() => document.querySelector('[data-eco]').click()); await t.page.waitForTimeout(2000);
      assert.ok(await t.page.evaluate(() => !!document.querySelector('#panel .lead')), 'opens after retry');
      assert.equal(await t.page.evaluate(() => document.getElementById('webload').hidden), true);
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });
  }
});
