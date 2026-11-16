import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';
await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGP4DwQACfsD/fteaysAAAAASUVORK5CYII=', 'base64');
const FAKE = 'abcdef012345.webp';   // a hosted file name that only exists in these tests

// Species pictures are our own hosted copies. A missing entry keeps the placeholder; nothing is ever fetched from another site.
// These tests never read the real hosted list (photos/species_hosted.json): the server answers every picture-entry request
// (api/species-pictures.json and the ph map of each place file) from `pics`, a small fixture {title: [file, page]} set per test.
describe('species pictures come only from our hosted copies', () => {
  let browser, srv, base, pics = {}, placePics = null, nodePic = false;   // placePics: null = the place file carries the same entries as pics; false = the place file has no picture entries at all (the app then reads the shared list)
  const slug = (latin) => latin.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');   // the species id: the slug of the Latin name (build/species.py)
  const speciesSid = slug(H.fixturePlace('/api/testland.json').nodes.find((n) => n.latin && !n.cat).latin);   // these tests use the made-up Testland (tests/fixtures), not a real place
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      if (u === '/photos/species-md/' + FAKE) { r.writeHead(200, { 'Content-Type': 'image/png' }); return r.end(testImage); }
      if (u === '/photos/nodes/' + FAKE) { r.writeHead(200, { 'Content-Type': 'image/png' }); return r.end(testImage); }   // a non-species node's picture is our own file under photos/nodes/ (#976)
      if (u.endsWith('/photos/places/places.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end('{}'); }   // no place photos: these tests are about species pictures
      if (u.endsWith('/api/species-pictures.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify({ ph: pics, phm: {} })); }
      if (fs.existsSync(path.join(H.FBUILD, u))) { const list = H.fixtureList(u, fs.readFileSync(path.join(H.FBUILD, u), 'utf8')); if (list) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(list); } }   // the fixture places are added to the world places
      if (/\/api\/[\w-]+\.json$/.test(u) && (H.fixturePlace(u) || fs.existsSync(path.join(H.FBUILD, u)))) {
        // give the place exactly the picture entries this test wants
        const w = H.fixturePlace(u) || JSON.parse(fs.readFileSync(path.join(H.FBUILD, u), 'utf8'));
        if (placePics === false) { delete w.ph; delete w.phm; } else { w.ph = { ...(placePics || pics) }; w.phm = {}; }
        if (nodePic) { w.nodes.find((n) => n.id === 'sun').wiki = 'Sunbeam'; w.ph = { ...(w.ph || {}), 'node:sunbeam': [FAKE, 'Sunbeam'] }; w.phm = { ...(w.phm || {}), 'node:sunbeam': { a: 'Test author', l: 'CC0', lu: '', p: 'https://commons.wikimedia.org/wiki/File:Sunbeam.jpg' } }; }   // the place file lists the picture under its node id
        r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify(w));
      }
      let f = path.join(H.FBUILD, u); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.FBUILD) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
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
      await t.page.goto(base + 'index.html#pg=testland');
      await t.page.waitForSelector('#pview article .pph svg', { timeout: 30000 });
      const place = await t.page.evaluate(() => ({
        heroIcon: !!document.querySelector('#pp-main svg'), heroPhoto: !!document.querySelector('#pp-main img'),
        speciesIcons: document.querySelectorAll('#pview .pph svg').length, speciesPhotos: document.querySelectorAll('#pview .pph img').length
      }));
      assert.ok(place.heroIcon && !place.heroPhoto, 'place hero keeps its placeholder');
      assert.ok(place.speciesIcons > 0 && place.speciesPhotos === 0, 'place page species cards keep their placeholders');
      await t.page.goto('about:blank');   // a fresh page: the journey pictures the place page may have loaded must not leak into this check
      await t.page.goto(base + 'index.html#e=testland');
      await t.page.waitForSelector('#svg .node .glyph', { timeout: 30000 });
      await t.page.waitForTimeout(1000);
      const species = await t.page.evaluate(() => ({ photos: document.querySelectorAll('#svg .node image.photo').length, icons: document.querySelectorAll('#svg .node .glyph').length }));
      assert.ok(species.icons > 0 && species.photos === 0, 'food-web species keep their placeholders ');
      assert.deepEqual(t.outside, [], 'nothing is requested from another site');
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: a listed species uses its hosted copy as a lazy thumbnail`, async () => {
      pics = { [speciesSid]: [FAKE, 'Test_page'] };
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=testland');
      await t.page.waitForFunction(() => document.querySelectorAll('#svg image.photo').length > 0, null, { timeout: 30000 });
      assert.ok(await t.page.locator('#svg image.photo[loading="lazy"]').count() > 0, 'food-web species photos are marked for native lazy loading');
      const href = await t.page.evaluate(() => document.querySelector('#svg image.photo').getAttribute('href'));
      assert.ok(href.endsWith('photos/species-md/' + FAKE) && !/^https?:/.test(href), 'the picture is our own file, read from our own site: ' + href);
      await t.page.goto(base + 'index.html#pg=testland');
      await t.page.waitForFunction(() => document.querySelectorAll('#pgraph image[loading="lazy"]').length > 0, null, { timeout: 30000 });
      assert.deepEqual(t.outside, []);
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: a picture listed under the species id shows for that species only (#974)`, async () => {
      const coyote = H.fixturePlace('/api/testland.json').nodes.find((n) => n.id === 'coyote');
      const sid = coyote.latin.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');   // the species id: the slug of the Latin name (build/species.py)
      pics = { [sid]: [FAKE, 'Test_page'] };
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=testland');
      await until(t.page, () => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'coyote'); return n && n.querySelector('image.photo[loading="lazy"]'); }, 'the coyote node to draw the picture listed under its species id');
      assert.ok((await nodeHref(t.page, 'coyote')).endsWith('photos/species-md/' + FAKE), 'the picture under the species id is the coyote\'s');
      const others = await t.page.evaluate(() => [...document.querySelectorAll('#svg .node')].filter((x) => x.__data__ && x.__data__.id !== 'coyote' && x.querySelector('image.photo')).length);
      assert.equal(others, 0, 'no other species shows a picture that is listed under another species id');
      assert.deepEqual(t.outside, []);
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });

    test(`${sizeName}: a picture in the shared list under the species id shows for that species (#973)`, async () => {
      const coyote = H.fixturePlace('/api/testland.json').nodes.find((n) => n.id === 'coyote');
      const sid = coyote.latin.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
      pics = { [sid]: [FAKE, 'Test_page'] }; placePics = false;   // only api/species-pictures.json has the entry: the place file carries none (an older place file)
      try {
        const t = await open(size);
        await t.page.goto(base + 'index.html#e=testland');
        await until(t.page, () => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'coyote'); return n && n.querySelector('image.photo[loading="lazy"]'); }, 'the coyote node to draw the picture the shared list has under its species id');
        assert.ok((await nodeHref(t.page, 'coyote')).endsWith('photos/species-md/' + FAKE));
        assert.deepEqual(t.outside, []);
        assert.deepEqual(t.errors, []);
        await t.ctx.close();
      } finally { placePics = null; }
    });

    test(`${sizeName}: a non-species node shows the picture listed under its node id, from photos/nodes/ (#976)`, async () => {
      pics = {}; nodePic = true;
      try {
        const t = await open(size);
        await t.page.goto(base + 'index.html#e=testland');
        await until(t.page, () => { const n = [...document.querySelectorAll('#svg .node')].find((x) => x.__data__ && x.__data__.id === 'sun'); return n && n.querySelector('image.photo'); }, 'the Sunlight node to draw the picture listed under its node id');
        const href = await nodeHref(t.page, 'sun');
        assert.ok(href.endsWith('photos/nodes/' + FAKE) && !/^https?:/.test(href), 'the node picture is our own file, read from our own site: ' + href);
        const others = await t.page.evaluate(() => [...document.querySelectorAll('#svg .node')].filter((x) => x.__data__ && x.__data__.id !== 'sun' && x.querySelector('image.photo')).length);
        assert.equal(others, 0, 'no other node shows that picture');
        assert.deepEqual(t.outside, []);
        assert.deepEqual(t.errors, []);
        await t.ctx.close();
      } finally { nodePic = false; }
    });

    // a title, an alias or a Latin name is no longer a key for a picture (#973 phase 4): the entries above are all by species id

    test(`${sizeName}: an entry that points to another site is never used`, async () => {
      const other = ['https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg', 'Test_page'];
      pics = { [speciesSid]: other };
      const t = await open(size);
      await t.page.goto(base + 'index.html#e=testland');
      await t.page.waitForSelector('#svg .node .glyph', { timeout: 30000 });
      await t.page.waitForTimeout(1500);
      assert.equal(await t.page.locator('#svg image.photo').count(), 0, 'no picture is drawn from another site');
      assert.deepEqual(t.outside, [], 'and nothing is requested from it');
      assert.deepEqual(t.errors, []);
      await t.ctx.close();
    });
  }
});
