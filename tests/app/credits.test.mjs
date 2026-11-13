import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

describe('credits', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });
  for (const [name, size] of Object.entries(H.SIZES)) {
    test(`${name}: link sits after the last place; dialog opens and closes three ways`, async () => {
      const t = await H.open(browser, H.FMAIN, size);
      if (name === 'phone') { await t.page.click('#shead'); await H.pause(t.page, 600); }
      const pos = await t.page.evaluate(() => {
        const c = document.querySelector('#cards'), l = document.getElementById('credbtn');
        return { after: !!(c.compareDocumentPosition(l) & Node.DOCUMENT_POSITION_FOLLOWING), cards: c.children.length };
      });
      assert.ok(pos.after && pos.cards > 0);
      await t.page.evaluate(() => document.getElementById('credbtn').scrollIntoView());
      await H.pause(t.page, 300);
      assert.ok(await t.page.isVisible('#credbtn'), 'link visible after scrolling to the end');
      for (const how of ['x', 'esc', 'backdrop']) {
        await t.page.click('#credbtn'); await H.pause(t.page, 250);
        assert.equal(await t.page.isVisible('#credmodal'), true, 'opens (' + how + ')');
        if (how === 'x') await t.page.click('#credx');
        else if (how === 'esc') await t.page.keyboard.press('Escape');
        else await t.page.mouse.click(3, 3);
        await H.pause(t.page, 250);
        assert.equal(await t.page.isVisible('#credmodal'), false, 'closes (' + how + ')');
      }
      await t.page.click('#credbtn'); await H.pause(t.page, 250);
      const box = await t.page.evaluate(() => { const r = document.querySelector('.credcard').getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: innerWidth, h: innerHeight }; });
      assert.ok(box.l >= 0 && box.r <= box.w && box.t >= 0 && box.b <= box.h, 'card fits on screen ' + JSON.stringify(box));
      await t.page.screenshot({ path: `${process.env.SHOT_DIR || '/tmp'}/credits-${name}.png` });
      assert.deepEqual(t.errors, []);
      await t.close();
    });
  }
});
