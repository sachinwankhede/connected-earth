import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';
await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.jpg': 'image/jpeg', '.js': 'text/javascript', '.png': 'image/png', '.webmanifest': 'application/json' };

describe('stored place photos carry a credit line', () => {
  let browser, srv, base;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      let f = path.join(H.FBUILD, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.FBUILD) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  const man = JSON.parse(fs.readFileSync(path.join(H.FDATA, 'photos/places/places.json'), 'utf8'));
  const places = H.readFixturePlaces(false).filter((e) => e.imgwiki && man[e.imgwiki] && fs.existsSync(path.join(H.FDATA, 'photos/places', man[e.imgwiki].f)));

  test('a picture list keyed by place id (the title in each row) shows the same picture and credit (#887)', async () => {
    const e = places[0], m = man[e.imgwiki];
    const byId = Object.fromEntries(places.map((x) => [x.id, { ...man[x.imgwiki], wiki: x.imgwiki }]));   // the new shape: key = place id, the title in `wiki`
    const ctx = await browser.newContext({ viewport: H.SIZES[Object.keys(H.SIZES)[0]] }); const page = await ctx.newPage();
    const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
    await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
    await page.route(/\/photos\/places\/places\.json(?:\?|$)/, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(byId) }));
    await page.goto(base + 'index.html#stub&pg=' + e.id); await page.reload();
    await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
    await page.waitForFunction(() => { const i = document.querySelector('#pp-main img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 60000 }).catch(() => {});
    const r = await page.evaluate(() => { const i = document.querySelector('#pp-main img'); const f = document.getElementById('pcredit'); if (!i) return null; return { src: i.getAttribute('src'), ok: i.naturalWidth > 0, cap: f ? f.textContent : '' }; });
    assert.ok(r, 'photo figure shown from an id-keyed list');
    assert.ok(r.src.includes('photos/places/' + m.f), 'served from our files: ' + r.src); assert.ok(r.ok, 'image loaded'); assert.ok(r.cap.includes(m.l.slice(0, 8)), 'licence shown: ' + r.cap);
    assert.deepEqual(errors, []);
    await ctx.close();
  });

  test('a place is found by its id: a row keyed by another place id with this place\'s title is not its picture (#968)', async () => {
    const a = places[0], b = places[1];
    assert.ok(b, 'the fixture has two places with pictures');
    // a's row under its own id; a second row under an unrelated id that carries b's title (two places on one title, #908): b has no row of its own
    const list = { [a.id]: { ...man[a.imgwiki], wiki: a.imgwiki }, 'someotherplace': { ...man[a.imgwiki], wiki: b.imgwiki } };
    const shows = async (e) => {
      const ctx = await browser.newContext({ viewport: H.SIZES[Object.keys(H.SIZES)[0]] }); const page = await ctx.newPage();
      const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
      await page.route(/\/photos\/places\/places\.json(?:\?|$)/, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(list) }));
      await page.goto(base + 'index.html#stub&pg=' + e.id); await page.reload();
      await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
      await page.waitForFunction(() => document.querySelector('#pp-main img'), null, { timeout: 15000 }).catch(() => {});
      const has = await page.evaluate(() => !!document.querySelector('#pp-main img'));
      assert.deepEqual(errors, []); await ctx.close(); return has;
    };
    assert.equal(await shows(a), true, 'the place with a row under its own id shows its picture');
    assert.equal(await shows(b), false, 'a place with no row under its own id shows no picture, whatever another row\'s title says');
  });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: photo comes from our own files, with author, licence and Commons link`, async () => {
      assert.ok(places.length > 0, 'at least one stored photo');
      const e = places[0], m = man[e.imgwiki];
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
      await page.goto(base + 'index.html#stub&pg=' + e.id); await page.reload();
      await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(2000);
      await page.waitForFunction(() => { const i = document.querySelector('#pp-main img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 60000 }).catch(() => {});
      const r = await page.evaluate(() => { const i = document.querySelector('#pp-main img'); const f = document.getElementById('pcredit'); if (!i) return null; return { src: i.getAttribute('src'), ok: i.naturalWidth > 0, cap: f.querySelector('ul').textContent, links: [...f.querySelectorAll('a')].map((a) => a.href) }; });
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
