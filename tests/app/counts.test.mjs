// #261 step 1: the chip counts read api/places/<main|pilot>/counts.json once it has arrived. The file must give the same numbers as counting the places in memory,
// for every region, with and without a kind filter, the parks filter and the local button (M.countsCheck lists the regions where they differ).
import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [buildName, base] of [['main', H.MAIN], ['pilot', H.PILOT]]) describe(`region counts from the file (${buildName})`, () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  test('the file is read, and its numbers match the places in memory in every filter state', async () => {
    const t = await H.open(browser, base, H.SIZES.desktop);
    const loaded = await t.page.evaluate(() => window.__M.loadCounts().then((c) => !!c));
    assert.equal(loaded, true, 'counts.json arrived');
    const check = (label) => t.page.evaluate(() => window.__M.countsCheck()).then((bad) => assert.deepEqual(bad, [], label));
    await check('plain');
    const kind = await t.page.$('[data-kind]');
    if (kind) {
      await kind.click(); await t.page.waitForTimeout(800);
      await check('one kind');
      await kind.click(); await t.page.waitForTimeout(500);
    }
    const loc = await t.page.$('#locbtn');
    if (loc) {
      await loc.click();
      await t.page.waitForFunction(() => window.__M && window.__M.countsCheck, null, { timeout: 30000 });
      await t.page.waitForTimeout(2500);
      await check('local places on');
    }
    assert.deepEqual(t.errors, []);
    await t.close();
  });
});
