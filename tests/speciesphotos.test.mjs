import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import * as H from './helper.mjs';

const approvedSpeciesPhotos = JSON.parse(fs.readFileSync(new URL('../photos/species.json', import.meta.url), 'utf8'));
const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGP4DwQACfsD/fteaysAAAAASUVORK5CYII=', 'base64');

// Missing photo entries keep the app's existing icons; listed entries use smaller approved thumbnail variants.
describe('photos use only stored manifests', () => {
  let browser, srv, base, title = '', approvedPhoto = null, directAsset = false;
  const speciesTitle = H.readPlaces(false).find((e) => e.id === 'yellowstone').nodes.find((n) => n.wiki).wiki;
  before(async () => {
    browser = await H.launch();
    srv = http.createServer((q, r) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      if (u.endsWith('/photos/species.json')) {
        const entry = directAsset
          ? ['https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg', 'Test_page']
          : approvedPhoto || ['9/99/Test.jpg/330px-Test.jpg', 'Test_page'];
        const titles = Array.isArray(title) ? title : title ? [title] : [];
        const manifest = Object.fromEntries(titles.map((t) => [t, entry]));
        r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end(JSON.stringify(manifest));
      }
      if (u.endsWith('/photos/places/places.json')) { r.writeHead(200, { 'Content-Type': 'application/json' }); return r.end('{}'); }
      let f = path.join(H.ROOT, u); if (f.endsWith('/')) f += 'index.html';
      if (!f.startsWith(H.ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html; charset=utf-8' : f.endsWith('.json') ? 'application/json' : 'application/octet-stream' }); r.end(fs.readFileSync(f));
    }).listen(0);
    base = `http://localhost:${srv.address().port}/`;
  });
  after(async () => { await browser.close(); srv.close(); });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: absent photos keep place and species placeholders without a Wikipedia lookup`, async () => {
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = [], lookups = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/wikipedia\.org\/api\/rest_v1\/page\/summary\//, (r) => { lookups.push(decodeURIComponent(r.request().url().split('/summary/')[1]).replace(/_/g, ' ')); r.abort(); });
      await page.route(/thumb\.wikimedia\.org/, (r) => r.abort());
      title = ''; approvedPhoto = null; directAsset = false;
      await page.goto(base + 'index.html#pg=yellowstone');
      await page.waitForFunction(() => window.__M && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
      await page.waitForSelector('#pview article .pph svg', { timeout: 30000 });
      const place = await page.evaluate(() => ({
        heroIcon: !!document.querySelector('#pp-main svg'),
        heroPhoto: !!document.querySelector('#pp-main img'),
        speciesIcons: document.querySelectorAll('#pview .pph svg').length,
        speciesPhotos: document.querySelectorAll('#pview .pph img').length
      }));
      assert.ok(place.heroIcon && !place.heroPhoto, 'place hero keeps its placeholder');
      assert.ok(place.speciesIcons > 0 && place.speciesPhotos === 0, 'place page species cards keep their placeholders');
      await page.goto(base + 'index.html#e=yellowstone');
      await page.waitForSelector('#svg .node .glyph', { timeout: 30000 });
      await page.waitForTimeout(1000);
      const species = await page.evaluate(() => ({
        icons: [...document.querySelectorAll('#svg .node .glyph')].filter((g) => getComputedStyle(g).display !== 'none').length,
        photos: document.querySelectorAll('#svg .node image.photo').length
      }));
      assert.ok(species.icons > 0 && species.photos === 0, 'food-web species keep their placeholders');
      assert.deepEqual(lookups, [], 'missing photos never trigger a Wikipedia API lookup');
      assert.deepEqual(errors, []);
      await ctx.close();
    });

    test(`${sizeName}: a listed species uses a smaller lazy thumbnail without a Wikipedia lookup`, async () => {
      directAsset = false;
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = [], lookups = [], thumbnails = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/wikipedia\.org\/api\/rest_v1\/page\/summary\//, (r) => { lookups.push(r.request().url()); r.abort(); });
      await page.route(/thumb\.wikimedia\.org/, (r) => {
        thumbnails.push(r.request().url());
        return r.fulfill({ status: 200, contentType: 'image/png', body: testImage });
      });
      title = speciesTitle; approvedPhoto = null;
      await page.goto(base + 'index.html#e=yellowstone');
      await page.waitForFunction(() => document.querySelectorAll('#svg image.photo').length > 0, null, { timeout: 30000 });
      const lazy = await page.locator('#svg image.photo[loading="lazy"]').count();
      assert.ok(lazy > 0, 'food-web species photos are marked for native lazy loading');
      assert.ok(thumbnails.some((u) => u.includes('9/99/Test.jpg/120px-Test.jpg')), 'smaller Wikimedia thumbnail variant requested');
      assert.deepEqual(lookups, [], 'listed photos do not need a Wikipedia API lookup');
      assert.deepEqual(errors, []);
      await page.goto(base + 'index.html#pg=yellowstone');
      await page.waitForFunction(() => document.querySelectorAll('#pgraph image[loading="lazy"]').length > 0, null, { timeout: 30000 });
      await ctx.close();
    });

    test(`${sizeName}: a species wiki alias uses its canonical approved photo`, async () => {
      directAsset = false;
      const dolphin = H.readPlaces(false).find((e) => e.id === 'gulf').nodes.find((n) => n.id === 'dolphin');
      assert.equal(dolphin.wiki, 'Bottlenose dolphin');
      assert.equal(dolphin.canonicalWiki, 'Common bottlenose dolphin');
      title = dolphin.canonicalWiki;
      approvedPhoto = approvedSpeciesPhotos[title];
      assert.ok(approvedPhoto, 'the canonical Wikipedia article has an approved photo');
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/thumb\.wikimedia\.org/, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: testImage }));
      await page.goto(base + 'index.html#e=gulf');
      await page.waitForFunction(() => {
        const dolphin = [...document.querySelectorAll('#svg .node')].find((n) => n.__data__ && n.__data__.id === 'dolphin');
        return dolphin && dolphin.querySelector('image.photo[loading="lazy"]');
      }, null, { timeout: 30000 });
      const webPhoto = await page.evaluate(() => {
        const dolphin = [...document.querySelectorAll('#svg .node')].find((n) => n.__data__ && n.__data__.id === 'dolphin');
        return dolphin && dolphin.querySelector('image.photo')?.getAttribute('href');
      });
      assert.ok(webPhoto && webPhoto.includes('/120px-Tursiops_truncatus_01-cropped.jpg'),
        'food web resolves the alias to the canonical article thumbnail');
      await page.goto(base + 'index.html#pg=gulf');
      await page.waitForFunction(() => document.querySelector('#pgraph .pn[data-node="dolphin"] image[loading="lazy"]'), null, { timeout: 30000 });
      assert.deepEqual(errors, []);
      await ctx.close();
      approvedPhoto = null;
    });

    test(`${sizeName}: the canonical Coyote photo key matches its common-name alias`, async () => {
      directAsset = false;
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = []; page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(/thumb\.wikimedia\.org/, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: testImage }));
      title = 'Canis latrans'; approvedPhoto = null;
      await page.goto(base + 'index.html#e=yellowstone');
      await page.waitForFunction(() => {
        const coyote = [...document.querySelectorAll('#svg .node')].find((n) => n.__data__ && n.__data__.id === 'coyote');
        return coyote && coyote.querySelector('image.photo[loading="lazy"]');
      }, null, { timeout: 30000 });
      const webPhoto = await page.evaluate(() => {
        const coyote = [...document.querySelectorAll('#svg .node')].find((n) => n.__data__ && n.__data__.id === 'coyote');
        return coyote && coyote.querySelector('image.photo')?.getAttribute('href');
      });
      assert.ok(webPhoto && webPhoto.includes('/120px-Test.jpg'), 'food web resolves the canonical Latin-keyed photo');
      await page.goto(base + 'index.html#pg=yellowstone');
      await page.waitForFunction(() => document.querySelector('#pgraph .pn[data-node="coyote"] image[loading="lazy"]'), null, { timeout: 30000 });
      assert.deepEqual(errors, []);
      await ctx.close();
    });

    test(`${sizeName}: an absolute Wikimedia asset URL is used unchanged`, async () => {
      const ctx = await browser.newContext({ viewport: size }); const page = await ctx.newPage();
      const errors = [], exact = 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg';
      page.on('pageerror', (x) => errors.push(String(x)));
      await page.route(/openfreemap|arcgis|amazonaws|fonts|cdnjs/, (r) => r.abort());
      await page.route(exact, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: testImage }));
      title = [speciesTitle, 'Osprey']; directAsset = true;
      await page.goto(base + 'index.html#e=yellowstone');
      await page.waitForFunction(() => {
        const image = document.querySelector('#svg image.photo');
        return image && image.getAttribute('href') === 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg';
      }, null, { timeout: 30000 });
      await page.goto(base + 'index.html#j=osprey');
      await page.waitForFunction(() => {
        const main = document.querySelector('#jview #jp-main img');
        const related = document.querySelector('#jview .jmore img');
        return main && related && main.src === 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Exact_file.jpg';
      }, null, { timeout: 30000 });
      assert.deepEqual(errors, []);
      directAsset = false;
      await ctx.close();
    });
  }
});
