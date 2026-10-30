import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

// A food web takes its species pictures from the stored list (photos/species.json) and asks Wikipedia only for species the list does not have.
describe('species pictures come from the stored list', () => {
  let browser, srv, base, title = '';
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      if (u.endsWith('/photos/species.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify(title ? { [title]: ['9/99/Test.jpg/330px-Test.jpg', 'Test_page'] } : {})); }
      let f = path.join(H.ROOT, u); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html; charset=utf-8' : f.endsWith('.json') ? 'application/json' : 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: a listed species gets its picture with no Wikipedia lookup`, async () => {
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = [], lookups = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/wikipedia\.org\/api\/rest_v1\/page\/summary\//, (r) => { lookups.push(decodeURIComponent(r.request().url().split('/summary/')[1]).replace(/_/g, ' ')); r.abort(); });
      await page.route(/thumb\.wikimedia\.org/, (r) => r.abort());
      const open = async () => { await page.goto(base + 'index.html#pg=yellowstone'); await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {}); await page.waitForTimeout(3500); };
      title = ''; await open();   // first with an empty list: Wikipedia is asked for the species of this place
      const first = [...lookups]; assert.ok(first.length > 0, 'the place asks Wikipedia when the list is empty');
      title = first[0]; lookups.length = 0; await open();
      assert.ok(!lookups.includes(title), 'no live lookup for the listed species: ' + lookups.slice(0, 5));
      assert.deepEqual(errors, []);
      await ctx.close();
    });
  }
});
