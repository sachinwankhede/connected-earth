import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

describe('map layers panel', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });
  for (const [name, size] of Object.entries(H.SIZES)) {
    test(`${name}: style buttons only; no shading button, no version label`, async () => {
      const t = await H.open(browser, H.FMAIN, size);
      await t.page.click('#lyrbtn'); await H.pause(t.page, 400);
      const r = await t.page.evaluate(() => ({
        shade: !!document.getElementById('shadebtn') || !!document.getElementById('shkey'),
        ver: !!document.getElementById('ver'),
        btns: [...document.querySelectorAll('#mapctl button')].filter((b) => b.offsetParent).map((b) => b.textContent.trim()),
        box: (() => { const x = document.getElementById('mapctl').getBoundingClientRect(); return { l: x.left, r: x.right, t: x.top, b: x.bottom, w: innerWidth, h: innerHeight }; })(),
      }));
      assert.equal(r.shade, false); assert.equal(r.ver, false);
      assert.deepEqual(r.btns, ['Light', 'Satellite', '3D']);
      assert.ok(r.box.l >= 0 && r.box.r <= r.box.w && r.box.t >= 0 && r.box.b <= r.box.h, 'panel on screen ' + JSON.stringify(r.box));
      for (const m of ['Light', 'Satellite']) { if (!(await t.page.isVisible('#mapctl'))) { await t.page.click('#lyrbtn'); await H.pause(t.page, 300); } await t.page.click(`#mapctl button:text-is("${m}")`); await H.pause(t.page, 1200); }
      assert.deepEqual(t.errors, []);
      await t.page.screenshot({ path: `${process.env.SHOT_DIR || '/tmp'}/layers-${name}.png` });
      await t.close();
    });
  }
});
