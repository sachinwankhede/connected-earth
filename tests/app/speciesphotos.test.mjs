import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const hosted = JSON.parse(fs.readFileSync(new URL('../../photos/species_hosted.json', import.meta.url), 'utf8'));
const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGP4DwQACfsD/fteaysAAAAASUVORK5CYII=', 'base64');
const FAKE = 'abcdef012345.webp';   // a hosted file name that only exists in these tests

// Species pictures are our own hosted copies. A missing entry keeps the placeholder; nothing is ever fetched from another site.
describe('species pictures come only from our hosted copies', () => {
  let browser, srv, base, titles = [], entry = null;
  const speciesTitle = H.readPlaces(false).find((e) => e.id === 'yellowstone').nodes.find((n) => n.wiki).wiki;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      if (u === '/photos/species/' + FAKE) { r.writeHead(200, { 'Content-Type': 'image/png' }); return r.end(testImage); }
      if (u.endsWith('/photos/places/places.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end('{}'); }   // no place photos: these tests are about species pictures
      if (/\/webs\/[\w-]+\.json$/.test(u) && !/(species-index|species-pictures)\.json$/.test(u) && entry !== undefined && titles !== null && fs.existsSync(path.join(H.ROOT, u))) {
        // give the place exactly the picture entries this test wants (null = leave the real ones)
        const w = JSON.parse(fs.readFileSync(path.join(H.ROOT, u), 'utf8'));
        w.ph = Object.fromEntries(titles.map((t) => [t, entry])); w.phm = {};
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
  const nodeHref = (page, id) => page.evaluate((id) => {
    const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === id);
    return n && n.querySelector('image.photo') ? n.querySelector('image.photo').getAttribute('href') : null;
  }, id);

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: absent photos keep place and species placeholders and read nothing from another site`, async () => {
      titles = []; entry = null;
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
      titles = [speciesTitle]; entry = [FAKE, 'Test_page'];
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
      titles = null; entry = null;   // the real entries the build wrote
      const dolphin = H.readPlaces(false).find((e) => e.id === 'gulf').nodes.find((n) => n.id === 'dolphin');
      assert.equal(dolphin.wiki, 'Bottlenose dolphin');
      assert.equal(dolphin.canonicalWiki, 'Common bottlenose dolphin');
      const want = hosted[dolphin.canonicalWiki];
      assert.ok(want, 'the canonical Wikipedia article has a hosted picture');
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=gulf');
      await t.page.waitForFunction(() => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'dolphin'); return n && n.querySelector('image.photo[loading="lazy"]'); }, null, { timeout: 60000 });
      const href = await nodeHref(t.page, 'dolphin');
      assert.ok(href && href.endsWith('photos/species/' + want), 'food web resolves the alias to the canonical hosted file: ' + href);
      await t.page.goto(base + 'index.html#pg=gulf');
      await t.page.waitForFunction(() => document.querySelector('#pgraph .pn[data-node="dolphin"] image[loading="lazy"]'), null, { timeout: 60000 });
      assert.deepEqual(t.outside, []);
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: the canonical Coyote picture key matches its common-name alias`, async () => {
      titles = null; entry = null;
      const want = hosted['Canis latrans'];
      assert.ok(want, 'Canis latrans has a hosted picture');
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=yellowstone');
      await t.page.waitForFunction(() => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'coyote'); return n && n.querySelector('image.photo[loading="lazy"]'); }, null, { timeout: 60000 });
      const href = await nodeHref(t.page, 'coyote');
      assert.ok(href && href.endsWith('photos/species/' + want), 'food web resolves the canonical Latin-keyed picture: ' + href);
      await t.page.goto(base + 'index.html#pg=yellowstone');
      await t.page.waitForFunction(() => document.querySelector('#pgraph .pn[data-node="coyote"] image[loading="lazy"]'), null, { timeout: 60000 });
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: an entry that points to another site is never used`, async () => {
      titles = [speciesTitle, 'Osprey']; entry = ['https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg', 'Test_page'];
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
