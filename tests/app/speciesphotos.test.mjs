import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGP4DwQACfsD/fteaysAAAAASUVORK5CYII=', 'base64');
const FAKE = 'abcdef012345.webp';   // a hosted file name that only exists in these tests

// Species pictures are our own hosted copies. A missing entry keeps the placeholder; nothing is ever fetched from another site.
// These tests never read the real hosted list (photos/species_hosted.json): the server answers every picture-entry request
// (api/species-pictures.json and the ph map of each place file) from `pics`, a small fixture {title: [file, page]} set per test.
describe('species pictures come only from our hosted copies', () => {
  let browser, srv, base, pics = {};
  const speciesTitle = H.readPlaces(false).find((e) => e.id === 'yellowstone').nodes.find((n) => n.wiki).wiki;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      if (u === '/photos/species/' + FAKE) { r.writeHead(200, { 'Content-Type': 'image/png' }); return r.end(testImage); }
      if (u.endsWith('/photos/places/places.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end('{}'); }   // no place photos: these tests are about species pictures
      if (u.endsWith('/api/species-pictures.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify({ ph: pics, phm: {} })); }
      if (/\/api\/[\w-]+\.json$/.test(u) && fs.existsSync(path.join(H.ROOT, u))) {
        // give the place exactly the picture entries this test wants
        const w = JSON.parse(fs.readFileSync(path.join(H.ROOT, u), 'utf8'));
        w.ph = { ...pics }; w.phm = {};
        r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify(w));
      }
      let f = path.join(H.ROOT, u); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
      const type = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.webp': 'image/webp' }[path.extname(f)] || 'application/octet-stream';
      r.writeHead(200, { 'Content-Type': type }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  async function open(size) {
    const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
    const errors = [], outside = []; page.on('pageerror', (x) => errors.push(String(x)));
    await page.route('**/*', (r) => {
      const u = new URL(r.request().url());
      if (u.hostname === 'localhost') return r.continue();
      if (!/openfreemap|arcgis|amazonaws|fonts|cdnjs/.test(u.hostname)) outside.push(u.href);
      return r.abort();
    });
    return { ctx, page, errors, outside };
  }
  // Wait for a condition in the page. A timeout names the stage that was reached (hash, diagram library, drawn nodes, place graph),
  // so a slow runner and a picture that never arrives can be told apart; the wait itself is never lengthened to hide a stall.
  async function until(page, fn, what, arg = null, timeout = 60000) {
    try { await page.waitForFunction(fn, arg, { timeout, polling: 100 }); }
    catch (e) {
      const where = await page.evaluate(() => ({ hash: location.hash, d3: typeof window.d3, nodes: document.querySelectorAll('#svg .node').length, photos: document.querySelectorAll('#svg image.photo').length, pgraph: !!document.querySelector('#pgraph'), pn: document.querySelectorAll('#pgraph .pn').length })).catch(() => 'page gone');
      throw new Error(`timed out waiting for ${what}; the page was at ${JSON.stringify(where)}`);
    }
  }
  const nodeHref = (page, id) => page.evaluate((id) => {
    const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === id);
    return n && n.querySelector('image.photo') ? n.querySelector('image.photo').getAttribute('href') : null;
  }, id);

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: absent photos keep place and species placeholders and read nothing from another site`, async () => {
      pics = {};
      const t = await open(size);
      await t.page.goto(base + 'index.html#pg=yellowstone');
      await t.page.waitForSelector('#pview article .pph svg', { timeout: 30000 });
      const place = await t.page.evaluate(() => ({
        heroIcon: !!document.querySelector('#pp-main svg'), heroPhoto: !!document.querySelector('#pp-main img'),
        speciesIcons: document.querySelectorAll('#pview .pph svg').length, speciesPhotos: document.querySelectorAll('#pview .pph img').length
      }));
      assert.ok(place.heroIcon && !place.heroPhoto, 'place hero keeps its placeholder');
      assert.ok(place.speciesIcons > 0 && place.speciesPhotos === 0, 'place page species cards keep their placeholders');
      await t.page.goto('about:blank');   // a fresh page: the journey pictures the place page may have loaded must not leak into this check
      await t.page.goto(base + 'index.html#e=yellowstone');
      await t.page.waitForSelector('#svg .node .glyph', { timeout: 30000 });
      await t.page.waitForTimeout(1000);
      const species = await t.page.evaluate(() => ({ photos: document.querySelectorAll('#svg .node image.photo').length, icons: document.querySelectorAll('#svg .node .glyph').length }));
      assert.ok(species.icons > 0 && species.photos === 0, 'food-web species keep their placeholders ');
      assert.deepEqual(t.outside, [], 'nothing is requested from another site');
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: a listed species uses its hosted copy as a lazy thumbnail`, async () => {
      pics = { [speciesTitle]: [FAKE, 'Test_page'] };
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=yellowstone');
      await t.page.waitForFunction(() => document.querySelectorAll('#svg image.photo').length > 0, null, { timeout: 30000 });
      assert.ok(await t.page.locator('#svg image.photo[loading="lazy"]').count() > 0, 'food-web species photos are marked for native lazy loading');
      const href = await t.page.evaluate(() => document.querySelector('#svg image.photo').getAttribute('href'));
      assert.ok(href.endsWith('photos/species/' + FAKE) && !/^https?:/.test(href), 'the picture is our own file, read from our own site: ' + href);
      await t.page.goto(base + 'index.html#pg=yellowstone');
      await t.page.waitForFunction(() => document.querySelectorAll('#pgraph image[loading="lazy"]').length > 0, null, { timeout: 30000 });
      assert.deepEqual(t.outside, []);
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: a species wiki alias uses its canonical hosted picture`, async () => {
      const dolphin = H.readPlaces(false).find((e) => e.id === 'gulf').nodes.find((n) => n.id === 'dolphin');
      assert.equal(dolphin.wiki, 'Bottlenose dolphin');
      assert.equal(dolphin.canonicalWiki, 'Common bottlenose dolphin');
      const want = FAKE;
      pics = { [dolphin.canonicalWiki]: [FAKE, 'Test_page'] };   // only the canonical article has a picture, the node itself is named by the alias
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=gulf');
      await until(t.page, () => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'dolphin'); return n && n.querySelector('image.photo[loading="lazy"]'); }, 'the dolphin node to draw its picture in the food web');
      const href = await nodeHref(t.page, 'dolphin');
      assert.ok(href && href.endsWith('photos/species/' + want), 'food web resolves the alias to the canonical hosted file: ' + href);
      await t.page.goto(base + 'index.html#pg=gulf');
      await until(t.page, () => document.querySelector('#pgraph .pn[data-node="dolphin"] image[loading="lazy"]'), 'the dolphin node to draw its picture in the place graph');
      assert.deepEqual(t.outside, []);
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: the canonical Coyote picture key matches its common-name alias`, async () => {
      const want = FAKE;
      pics = { 'Canis latrans': [FAKE, 'Test_page'] };   // keyed by the Latin name only
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=yellowstone');
      await until(t.page, () => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'coyote'); return n && n.querySelector('image.photo[loading="lazy"]'); }, 'the coyote node to draw its picture in the food web');
      const href = await nodeHref(t.page, 'coyote');
      assert.ok(href && href.endsWith('photos/species/' + want), 'food web resolves the canonical Latin-keyed picture: ' + href);
      await t.page.goto(base + 'index.html#pg=yellowstone');
      await until(t.page, () => document.querySelector('#pgraph .pn[data-node="coyote"] image[loading="lazy"]'), 'the coyote node to draw its picture in the place graph');
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: an entry that points to another site is never used`, async () => {
      const other = ['https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg', 'Test_page'];
      pics = { [speciesTitle]: other, Osprey: other };
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=yellowstone');
      await t.page.waitForSelector('#svg .node .glyph', { timeout: 30000 });
      await t.page.waitForTimeout(1500);
      assert.equal(await t.page.locator('#svg image.photo').count(), 0, 'no picture is drawn from another site');
      assert.deepEqual(t.outside, [], 'and nothing is requested from it');
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });
  }
});
