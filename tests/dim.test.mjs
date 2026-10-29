import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

// A chip dims when no place of that habitat is inside the map view (after the map settles).
describe('chip dimming follows the map', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  const views = [['world', [0, 20], 1], ['Missouri', [-91, 38.6], 8], ['Serengeti', [34.8, -2.4], 6], ['mid-Pacific', [-150, 0], 3.5], ['Antarctica', [20, -80], 3], ['Alps', [10, 46.5], 7], ['Sahara', [10, 25], 5]];

  async function check(t, places, localOn) {
    for (const [name, c, z] of views) {
      await H.jump(t.page, c, z);
      const bd = await t.page.evaluate(() => { const b = window.__M.map.getBounds(); return [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]; });
      const expected = Object.keys(H.GROUPS).filter((g) => !places.some((e) =>
        H.GROUPS[g].includes(e.kind) && (localOn || e.level !== 'local') && (!(e.auto && e.level !== 'local') || z >= 3.5) &&
        e.lon >= bd[0] && e.lon <= bd[2] && e.lat >= bd[1] && e.lat <= bd[3])).sort();
      assert.deepEqual(await H.dimmed(t.page), expected, `${name} (local ${localOn ? 'on' : 'off'})`);
    }
  }

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: main app`, async () => {
      const t = await H.open(browser, H.MAIN, size);
      await check(t, H.readPlaces(false), false);
      assert.deepEqual(t.errors, []);
      await t.close();
    });
    test(`${sizeName}: pilot, local parks off then on`, async () => {
      const t = await H.open(browser, H.PILOT, size);
      const places = H.readPlaces(true);
      await check(t, places, false);
      await t.page.click('#locbtn');
      for (let i = 0; ; i++) {   // the chips settle after the map finishes moving; retry instead of a fixed wait
        await t.page.waitForTimeout(500);
        try { await check(t, places, true); break; } catch (e) { if (i >= 8) throw e; }
      }
      assert.deepEqual(t.errors, []);
      await t.close();
    });
    test(`${sizeName}: tapping a dimmed chip selects it and brings the map to that habitat`, async () => {
      const t = await H.open(browser, H.MAIN, size);
      await H.jump(t.page, [-91, 38.6], 8);
      const d = await H.dimmed(t.page);
      assert.ok(d.length > 0);
      await t.page.click(`[data-kind="${d[0]}"]`); await t.page.waitForTimeout(1800);
      assert.equal(await t.page.getAttribute(`[data-kind="${d[0]}"]`, 'aria-pressed'), 'true');
      assert.ok(!(await H.dimmed(t.page)).includes(d[0]), 'a selected chip is never dimmed');
      await t.close();
    });
  }
});
