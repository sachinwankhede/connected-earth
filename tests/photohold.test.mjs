import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

// Pictures wait for the map: nothing is asked for until the map has drawn, the person touches the page, or a link goes straight to a place.
describe('pictures wait for the map', () => {
  let browser, srv, base;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      let f = path.join(H.ROOT, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html; charset=utf-8' : f.endsWith('.json') ? 'application/json' : f.endsWith('.jpg') ? 'image/jpeg' : 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: no picture request before the map has drawn; a touch releases them`, async () => {
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = [], pics = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/openfreemap|arcgis/, () => {});   // these requests never answer, so the map never finishes drawing
      page.on('request', (r) => { if (/photos\/places\/.+\.jpg|rest_v1\/page\/summary|thumb\.wikimedia/.test(r.url())) pics.push(r.url()); });
      await page.route(/wikipedia|wikimedia/, (r) => r.abort());
      await page.goto(base + 'index.html', { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(4000);
      assert.deepEqual(pics, [], 'nothing asked for while the map is still drawing');
      await page.mouse.click(size.width / 2, size.height / 2); await page.waitForTimeout(2500);
      assert.ok(pics.length > 0, 'pictures are asked for after a touch');
      assert.deepEqual(errors, []);
      await ctx.close();
    });
  }
  test('desktop: a link straight to a place loads its picture at once', async () => {
    const ctx = await browser.newContext({ viewport: H.SIZES.desktop }); const page = await ctx.newPage();
    const pics = [];
    await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
    page.on('request', (r) => { if (/photos\/places\/.+\.jpg/.test(r.url())) pics.push(r.url()); });
    await page.goto(base + 'index.html#pg=yellowstone'); await page.waitForTimeout(3000);
    assert.ok(pics.length > 0, 'the place picture was requested without waiting');
    await ctx.close();
  });
});
