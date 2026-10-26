import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

describe('place sheet', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: open a place, pick a species, clear it, open sources`, async () => {
      const t = await H.open(browser, H.MAIN, size, { hash: '#stub&e=npmammothcave' });
      if (sizeName === 'phone') { await t.page.click('#phead'); await t.page.waitForTimeout(600); }
      assert.match(await t.page.textContent('#panel h2, #panel .lead') || '', /./);
      await t.page.click('#panel .chips .chip >> nth=0');
      await t.page.waitForTimeout(1000);
      const picked = await t.page.evaluate(() => ({ h2: document.querySelector('#panel h2')?.textContent, sel: document.querySelectorAll('.node.sel,.node.on').length }));
      assert.ok(picked.h2, 'species name shown');
      assert.equal(picked.sel, 1, 'exactly one species selected in the graph');
      await t.page.keyboard.press('Escape');
      await t.page.waitForTimeout(500);
      assert.equal(await t.page.evaluate(() => !!document.querySelector('#panel .lead')), true, 'back to the place overview');
      assert.equal(await t.page.evaluate(() => !!document.querySelector('.autotag')), false, 'hand-built place has no auto-generated tag');
      if (sizeName === 'phone') { await t.page.click('#phead'); await t.page.waitForTimeout(400); }
      await t.page.click('#panel details summary');
      assert.equal(await t.page.evaluate(() => document.querySelector('#panel details').open), true);
      assert.deepEqual(t.errors, []);
      await t.close();
    });

    test(`${sizeName}: auto-generated places show no tag (the flag stays in the data)`, async () => {
      const t = await H.open(browser, H.PILOT, size, { hash: '#stub&e=mocastlewood' });
      assert.equal(await t.page.evaluate(() => !!document.querySelector('.autotag')), false);
      assert.ok(await t.page.evaluate(() => !!document.querySelector('#panel .lead')), 'place sheet opened');
      assert.deepEqual(t.errors, []);
      await t.close();
    });
  }
});
