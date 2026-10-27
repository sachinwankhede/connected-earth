import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

// The base map (street or satellite tiles) can fail while the app is open. The app should quietly fall back and recover.
const style = (src) => JSON.stringify({ version: 8, name: 't', glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf', sources: { openmaptiles: src }, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#dde' } }, { id: 'lines', type: 'line', source: 'openmaptiles', 'source-layer': 'boundary' }] });
const tj = (up) => ({ type: 'vector', tiles: ['https://tiles.openfreemap.org/t/{z}/{x}/{y}.pbf'] });

describe('base map fallback', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  async function open(size, { vectorOk, satOk, retryMs }) {
    const ctx = await browser.newContext({ viewport: size });
    const page = await ctx.newPage(); const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    let vOk = vectorOk, sOk = satOk;
    await page.route(/wikipedia|wikimedia|fonts\.|cdnjs/, (r) => r.abort());
    await page.route(/openfreemap\.org\/styles\//, (r) => r.fulfill({ contentType: 'application/json', body: style(tj()) }));
    await page.route(/openfreemap\.org\/planet/, (r) => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ tilejson: '2.0.0', tiles: ['https://tiles.openfreemap.org/t/{z}/{x}/{y}.pbf'], vector_layers: [] }) }));
    await page.route(/openfreemap\.org\/t\//, (r) => (vOk ? r.fulfill({ status: 200, contentType: 'application/x-protobuf', body: '' }) : r.abort()));
    await page.route(/openfreemap\.org\/fonts/, (r) => r.abort());
    await page.route(/arcgisonline/, (r) => (sOk ? r.fulfill({ status: 404 }) && undefined : r.abort()));
    await page.addInitScript((ms) => { if (ms) window.__retryMs = ms; }, retryMs);
    await page.goto(await H.urlFor(H.MAIN));
    await page.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 90000 }).catch(() => {});
    return { ctx, page, errors, set: (v, s) => { vOk = v; sOk = s; } };
  }
  const state = (page) => page.evaluate(() => ({ mode: window.__M.mode, stub: !!window.__M.stub, nobase: document.getElementById('map').classList.contains('nobase'), dots: document.querySelectorAll('.maplibregl-canvas').length }));
  const wait = (page, f) => page.waitForFunction(f, null, { timeout: 90000 });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: satellite fails, street map still works -> streets, no plain map`, async () => {
      const t = await open(size, { vectorOk: true, satOk: false });
      await H.jump(t.page, [10, 45], 5); await t.page.waitForTimeout(500);
      await wait(t.page, () => window.__M.mode === 'streets');
      const s = await state(t.page);
      assert.equal(s.stub, false); assert.equal(s.nobase, false);
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });

    test(`${sizeName}: all tiles fail -> plain map, then the real map returns when tiles recover`, async () => {
      const t = await open(size, { vectorOk: false, satOk: false, retryMs: 2500 });
      await H.jump(t.page, [10, 45], 5);
      await wait(t.page, () => window.__M.stub === true);
      assert.equal((await state(t.page)).nobase, true);
      assert.ok((await H.dots(t.page)) >= 0);
      t.set(true, true);
      await wait(t.page, () => window.__M.stub === false && window.__M.styleReady);
      assert.equal((await state(t.page)).nobase, false);
      assert.deepEqual(t.errors, []); await t.ctx.close();
    });
  }
});
