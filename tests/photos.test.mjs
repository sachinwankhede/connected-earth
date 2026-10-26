import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.jpg': 'image/jpeg', '.js': 'text/javascript', '.png': 'image/png', '.webmanifest': 'application/json' };

describe('stored place photos carry a credit line', () => {
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

  const man = JSON.parse(fs.readFileSync(path.join(H.ROOT, 'photos/places/places.json'), 'utf8'));
  const places = H.readPlaces(false).filter((e) => e.imgwiki && man[e.imgwiki] && fs.existsSync(path.join(H.ROOT, 'photos/places', man[e.imgwiki].f)));

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: photo comes from our own files, with author, licence and Commons link`, async () => {
      assert.ok(places.length > 0, 'at least one stored photo');
      const e = places[0], m = man[e.imgwiki];
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
      await page.goto(base + 'index.html#stub&e=' + e.id); await page.reload();
      await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(2000);
      if (sizeName === 'phone') { await page.click('#phead'); await page.waitForTimeout(600); }
      const r = await page.evaluate(() => { const f = document.querySelector('#panel .shot'); if (!f) return null; const i = f.querySelector('img'); return { src: i.getAttribute('src'), ok: i.naturalWidth > 0, cap: f.querySelector('figcaption').textContent, links: [...f.querySelectorAll('figcaption a')].map((a) => a.href) }; });
      assert.ok(r, 'photo figure shown');
      assert.ok(r.src.includes('photos/places/' + m.f), 'served from our files: ' + r.src);
      assert.ok(r.ok, 'image loaded');
      assert.match(r.cap, /^Photo: /); assert.ok(r.cap.includes(m.l.slice(0, 8)), 'licence shown: ' + r.cap); assert.match(r.cap, /Wikimedia Commons/);
      assert.ok(r.links.some((l) => l.includes('commons.wikimedia.org/wiki/File:')), 'link to the file page');
      assert.deepEqual(errors, []);
      await page.screenshot({ path: `${process.env.SHOT_DIR || '/tmp'}/photo-credit-${sizeName}.png` });
      await ctx.close();
    });
  }
});
