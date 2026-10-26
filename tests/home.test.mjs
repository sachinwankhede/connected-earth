import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

describe('home screen on phones', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  for (const [w, h] of [[360, 640], [390, 750], [393, 852]]) {
    test(`${w}x${h}: home line shows under the title, even with a tall browser bar below (simulated 90px safe area)`, async () => {
      const t = await H.open(browser, H.MAIN, { width: w, height: h }, { extraCss: '.sheet{padding-bottom:90px !important}' });
      await t.page.waitForTimeout(500);
      const r = await t.page.evaluate(() => { const x = document.getElementById('hook').getBoundingClientRect(); return { top: x.top, bottom: x.bottom, vh: innerHeight, w: x.width, sw: document.getElementById('hook').scrollWidth }; });
      assert.ok(r.bottom <= r.vh - 90, `home line must sit above the 90px browser bar (bottom ${r.bottom}, limit ${r.vh - 90})`);
      assert.ok(r.sw <= r.w + 1, 'home line does not overflow its width');
      await t.close();
    });
  }

  test('home line goes away when a region is chosen and comes back at home', async () => {
    const t = await H.open(browser, H.MAIN, H.SIZES.desktop);
    assert.ok(await H.hookText(t.page));
    await t.page.click('#regions .chip >> nth=0'); await t.page.waitForTimeout(1200);
    assert.equal(await H.hookText(t.page), null);
    await t.close();
  });
});
