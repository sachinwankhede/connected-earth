import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';
await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

for (const [buildName, isPilot] of [['main', false], ['pilot', true]]) describe(`local parks (${buildName})`, () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });
  const places = H.readFixturePlaces(isPilot);
  const local = places.filter((e) => e.level === 'local');
  const national = places.filter((e) => e.level !== 'local');

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: the button adds and removes the local parks, and the home line follows`, async () => {
      const t = await H.open(browser, isPilot ? H.FPILOT : H.FMAIN, size);
      assert.ok(local.length > 0);
      assert.equal(await t.page.getAttribute('#locbtn', 'aria-pressed'), 'false');
      assert.equal(await H.hookText(t.page), H.HOOK);
      const before = await H.dots(t.page);
      await t.page.click('#locbtn');
      assert.equal(await H.dotsEq(t.page, before + local.length), before + local.length);
      assert.equal(await t.page.getAttribute('#locbtn', 'aria-pressed'), 'true');
      assert.equal(await H.hookText(t.page), H.HOOK);
      await t.page.click('#locbtn');
      assert.equal(await H.dotsEq(t.page, before), before);
      assert.deepEqual(t.errors, []);
      await t.close();
    });

    test(`${sizeName}: search finds a local park even with the button off`, async () => {
      const t = await H.open(browser, isPilot ? H.FPILOT : H.FMAIN, size);
      await t.page.fill('#q', 'castlewood');
      await t.page.waitForFunction(() => { const s = window.__M.map.getSource('atl-e'); return s && ((s._data && s._data.features) || []).length >= 1; }, null, { timeout: 30000 }).catch(() => {});
      assert.ok((await H.dots(t.page)) >= 1);
      assert.equal(await H.hookText(t.page), null, 'home line hidden while searching');
      await t.close();
    });

    test(`${sizeName}: Near me lists local parks even with the button off`, async () => {
      const t = await H.open(browser, isPilot ? H.FPILOT : H.FMAIN, size, { geo: { latitude: 38.5481, longitude: -90.5433 } });
      await t.page.click('#znear');
      await t.page.waitForFunction(() => document.querySelectorAll('.nearlist .nrow b').length > 0, null, { timeout: 30000 }).catch(() => {});
      const rows = await t.page.evaluate(() => [...document.querySelectorAll('.nearlist .nrow b')].map((x) => x.textContent));
      assert.ok(rows.includes('Castlewood'), 'nearest list: ' + rows.join(', '));
      await t.close();
    });
  }
});
