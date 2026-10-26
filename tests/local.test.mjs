import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [buildName, isPilot] of [['main', false], ['pilot', true]]) describe(`local parks (${buildName})`, () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });
  const places = H.readPlaces(isPilot);
  const local = places.filter((e) => e.level === 'local');
  const national = places.filter((e) => e.level !== 'local');

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: the button adds and removes the local parks, and the home line follows`, async () => {
      const t = await H.open(browser, isPilot ? H.PILOT : H.MAIN, size);
      assert.ok(local.length > 0);
      assert.equal(await t.page.getAttribute('#locbtn', 'aria-pressed'), 'false');
      assert.equal(await H.hookText(t.page), H.expectedHook(national));
      const before = await H.dots(t.page);
      await t.page.click('#locbtn'); await t.page.waitForTimeout(900);
      assert.equal(await t.page.getAttribute('#locbtn', 'aria-pressed'), 'true');
      assert.equal(await H.dots(t.page), before + local.length);
      assert.equal(await H.hookText(t.page), H.expectedHook(places));
      await t.page.click('#locbtn'); await t.page.waitForTimeout(700);
      assert.equal(await H.dots(t.page), before);
      assert.deepEqual(t.errors, []);
      await t.close();
    });

    test(`${sizeName}: search finds a local park even with the button off`, async () => {
      const t = await H.open(browser, isPilot ? H.PILOT : H.MAIN, size);
      await t.page.fill('#q', 'castlewood'); await t.page.waitForTimeout(800);
      assert.ok((await H.dots(t.page)) >= 1);
      assert.equal(await H.hookText(t.page), null, 'home line hidden while searching');
      await t.close();
    });

    test(`${sizeName}: Near me lists local parks even with the button off`, async () => {
      const t = await H.open(browser, isPilot ? H.PILOT : H.MAIN, size, { geo: { latitude: 38.5481, longitude: -90.5433 } });
      await t.page.click('#znear'); await t.page.waitForTimeout(2500);
      const rows = await t.page.evaluate(() => [...document.querySelectorAll('.nearlist .nrow b')].map((x) => x.textContent));
      assert.ok(rows.includes('Castlewood'), 'nearest list: ' + rows.join(', '));
      await t.close();
    });
  }
});
