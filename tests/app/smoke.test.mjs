import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

describe('smoke: every build loads cleanly on phone and desktop', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  for (const [buildName, file, pilot] of [['main', H.MAIN, false], ['pilot', H.PILOT, true]]) {
    for (const [sizeName, size] of Object.entries(H.SIZES)) {
      test(`${buildName} / ${sizeName}: loads, no page errors, home line matches the data`, async () => {
        const t = await H.open(browser, file, size);
        assert.deepEqual(t.errors, []);
        const places = H.readPlaces(pilot);
        const visible = places.filter((e) => e.level !== 'local');
        assert.equal(await H.hookText(t.page), H.HOOK);
        // phone: the line must be visible without opening the sheet
        const inView = await t.page.evaluate(() => { const r = document.getElementById('hook').getBoundingClientRect(); return r.height > 0 && r.bottom <= innerHeight; });
        assert.ok(inView, 'home line should be on screen when the app opens');
        await t.close();
      });
    }
  }

  test('main app: local-parks button shows when local parks exist; national auto places wait for zoom', async () => {
    const t = await H.open(browser, H.MAIN, H.SIZES.phone);
    const places = H.readPlaces(false), hasLocal = places.some((e) => e.level === 'local');
    assert.equal(await t.page.evaluate(() => getComputedStyle(document.getElementById('locbtn')).display) !== 'none', hasLocal);
    assert.equal(await t.page.evaluate(() => window.__M.map.getSource('atl-e')._data.features.length + window.__M.map.getSource('atl-f')._data.features.length), H.atWorld(places).length);
    await t.close();
  });
});
