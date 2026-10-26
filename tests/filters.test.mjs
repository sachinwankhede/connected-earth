import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

describe('habitat chips', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });
  const places = H.atWorld(H.readPlaces(false));

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: five short chips, no counts, no "Protected areas"`, async () => {
      const t = await H.open(browser, H.MAIN, size);
      const labels = await H.chipLabels(t.page);
      assert.deepEqual(labels, Object.keys(H.GROUPS));
      assert.ok(labels.every((l) => !/\d/.test(l)), 'no counts on chips');
      await t.close();
    });

    test(`${sizeName}: each chip filters to its habitats and switches off again`, async () => {
      const t = await H.open(browser, H.MAIN, size);
      const all = await H.dots(t.page);
      assert.equal(all, places.length);
      for (const [label, kinds] of Object.entries(H.GROUPS)) {
        await t.page.click(`[data-kind="${label}"]`); await t.page.waitForTimeout(900);
        assert.equal(await H.dots(t.page), places.filter((e) => kinds.includes(e.kind)).length, label);
        assert.equal(await t.page.getAttribute(`[data-kind="${label}"]`, 'aria-pressed'), 'true');
        await t.page.click(`[data-kind="${label}"]`); await t.page.waitForTimeout(600);
        assert.equal(await H.dots(t.page), all, label + ' off');
      }
      assert.deepEqual(t.errors, []);
      await t.close();
    });

    test(`${sizeName}: a filter keeps the camera if something is in view, moves it if nothing is`, async () => {
      const t = await H.open(browser, H.PILOT, size);
      await H.jump(t.page, [-91, 38.6], 8);
      const start = await H.camera(t.page);
      await t.page.click('#locbtn'); await t.page.waitForTimeout(1200);
      assert.deepEqual(await H.camera(t.page), start, 'Local parks button keeps the camera');
      await t.page.click('[data-kind="Forest"]'); await t.page.waitForTimeout(1500);
      assert.deepEqual(await H.camera(t.page), start, 'Forest chip keeps the camera (forests are in view)');
      await t.page.click('[data-kind="Forest"]'); await t.page.waitForTimeout(800);
      await t.page.click('[data-kind="Cold & high"]'); await t.page.waitForTimeout(1800);
      const moved = await H.camera(t.page);
      assert.ok(moved.zoom < start.zoom - 2, 'nothing cold or high nearby: the map zooms out to find some');
      await t.close();
    });
  }
});
