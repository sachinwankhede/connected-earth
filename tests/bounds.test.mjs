import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json' };
// Opening a US place outlines its real boundary and fits the map to it; closing the card clears it. Other places are untouched.
describe('real park outlines', () => {
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

  const B = JSON.parse(fs.readFileSync(path.join(H.ROOT, 'data/bounds.json'), 'utf8'));
  const all = H.readPlaces(true);
  const withB = all.filter((e) => B[e.id] && !e.auto).slice(0, 1).concat(all.filter((e) => B[e.id] && e.level === 'local').slice(0, 1), all.filter((e) => B[e.id] && e.auto && e.level !== 'local').slice(0, 1));
  const without = all.find((e) => !B[e.id] && e.country !== 'United States of America' && !e.auto);

  async function open(size, id, file = 'index.html') {
    const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
    const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
    await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
    await page.goto(base + file + '#stub&p=' + id); await page.reload();
    await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(2500);
    return { ctx, page, errors };
  }
  const outline = (page) => page.evaluate(() => { const s = window.__M.map.getSource('atl-bound'); const d = s && s._data; return d && d.features ? d.features.length : -1; });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: places with an outline show it, fit the map to it, and clear it on close`, async () => {
      assert.ok(withB.length >= 2, 'need places with outlines');
      for (const e of withB) {
        const t = await open(size, e.id, e.auto && e.level !== 'local' && !H.readPlaces(false).some((x) => x.id === e.id) ? 'pilot/index.html' : 'index.html');
        const n = await outline(t.page);
        assert.equal(n, B[e.id].r.length, `${e.id}: outline drawn`);
        await t.page.waitForTimeout(900);
        const inView = await t.page.evaluate(([x0, y0, x1, y1]) => { const b = window.__M.map.getBounds(); return b.getWest() <= x0 + 1e-6 && b.getEast() >= x1 - 1e-6 && b.getSouth() <= y0 + 1e-6 && b.getNorth() >= y1 - 1e-6; }, (() => { let a = 999, b = 99, c = -999, d = -99; for (const f of B[e.id].r) for (let i = 0; i < f.length; i += 2) { a = Math.min(a, f[i]); c = Math.max(c, f[i]); b = Math.min(b, f[i + 1]); d = Math.max(d, f[i + 1]); } return [a, b, c, d]; })());
        assert.ok(inView, `${e.id}: the whole outline is in view`);
        assert.match(await t.page.textContent('#peek'), /Outlined on the map/);
        await t.page.evaluate(() => document.querySelector('[data-closepeek]').click()); await t.page.waitForTimeout(1200);
        assert.equal(await outline(t.page), 0, `${e.id}: outline cleared on close`);
        assert.deepEqual(t.errors, []); await t.ctx.close();
      }
    });
    test(`${sizeName}: a place without an outline just opens as before`, async () => {
      assert.ok(without, 'a non-US place exists');
      const t = await open(size, without.id);
      assert.equal(await outline(t.page), 0);
      assert.equal(await t.page.evaluate(() => !document.getElementById('peek').hidden), true, 'card is open');
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });
  }
});
