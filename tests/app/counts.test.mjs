// #261 steps 1 and 2: the chip counts read api/places/<main|pilot>/counts.json once it has arrived. The file must give the same numbers as counting the places in memory,
// for every region, with and without a kind filter, the parks filter and the local button (M.countsCheck lists the regions where they differ). Step 2: the chips that appear
// (continents, then countries, then US states) come from the same file and must be the same list as the one from the places in memory (M.listsCheck).
import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

for (const [buildName, base] of [['main', H.FMAIN], ['pilot', H.FPILOT]]) describe(`region counts from the file (${buildName})`, () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  test('the file is read, and its numbers match the places in memory in every filter state', async () => {
    const t = await H.open(browser, base, H.SIZES.desktop);
    const loaded = await t.page.evaluate(() => window.__M.loadCounts().then((c) => !!c));
    assert.equal(loaded, true, 'counts.json arrived');
    const check = (label) => t.page.evaluate(() => window.__M.countsCheck()).then((bad) => assert.deepEqual(bad, [], label));
    await check('plain');
    if (await t.page.$('[data-kind]')) {   // the chips are drawn again after each click, so find the first one each time
      await t.page.click('[data-kind]'); await H.pause(t.page, 800);
      await check('one kind');
      await t.page.click('[data-kind]'); await H.pause(t.page, 500);
    }
    if (await t.page.$('#locbtn')) {
      await t.page.click('#locbtn');
      await t.page.waitForFunction(() => window.__M && window.__M.countsCheck, null, { timeout: 30000 });
      await H.pause(t.page, 2500);
      await check('local places on');
    }
    assert.deepEqual(t.errors, []);
    await t.close();
  });
  test('the chips that appear are the same from the file and from the places in memory', async () => {
    const t = await H.open(browser, base, H.SIZES.desktop);
    assert.equal(await t.page.evaluate(() => window.__M.loadCounts().then((c) => !!c)), true, 'counts.json arrived');
    const lists = async (label) => assert.deepEqual(await t.page.evaluate(() => window.__M.listsCheck()), [], label);
    const chips = (lvl) => t.page.$$eval(`[data-go="${lvl}"][data-a]`, (b) => b.length);
    assert.ok(await chips('continent') > 1, 'continent chips at the world view');
    await lists('continents');
    await t.page.click('[data-kind]'); await H.pause(t.page, 800);
    await lists('continents, one kind');
    await t.page.click('[data-kind]'); await H.pause(t.page, 500);
    await t.page.click('[data-go="continent"][data-a="North America"]'); await H.pause(t.page, 1500);
    assert.ok(await chips('country') > 0, 'country chips in North America');
    await lists('countries of North America');
    const us = '[data-go="country"][data-a="United States of America"]';
    if (await t.page.$(us)) {
      await t.page.click(us); await H.pause(t.page, 1500);
      assert.ok(await chips('state') > 1, 'state chips in the United States');
      await lists('US states');
      await t.page.click('[data-kind]'); await H.pause(t.page, 800);
      await lists('US states, one kind');
    }
    assert.deepEqual(t.errors, []);
    await t.close();
  });
});
