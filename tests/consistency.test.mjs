import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

// docs/DESIGN.md: one back link, same look and place on every screen.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: every screen has one back link that looks and sits the same`, async () => {
    const b = await H.launch();
    const seen = [];
    for (const [scr, hash] of [['place', '#stub&pg=yellowstone'], ['explore', '#stub&e=yellowstone'], ['journey', '#stub']]) {
      const t = await H.open(b, H.MAIN, size, { hash }); const p = t.page;
      if (scr === 'journey') await p.evaluate(() => window.__M.showJourney(window.__M.journeyIds()[0]));
      await p.waitForSelector(scr === 'explore' ? '#pbk' : '.jback', { state: 'visible', timeout: 60000 });
      const r = await p.evaluate(() => {
        const q = [...document.querySelectorAll('.jback,#pbk,#back')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
        return q.map((e) => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return { t: e.textContent.trim(), x: Math.round(r.x), h: Math.round(r.height), fs: c.fontSize, fw: c.fontWeight, col: c.color }; });
      });
      assert.equal(r.length, 1, `${scr}: exactly one back link, got ${JSON.stringify(r)}`);
      assert.match(r[0].t, /^‹ \S/, `${scr}: "‹ Destination"`);
      seen.push({ scr, ...r[0] });
      assert.deepEqual(t.errors, []); await t.close();
    }
    for (const k of ['h', 'fs', 'fw', 'col']) assert.equal(new Set(seen.map((s) => s[k])).size, 1, `back link ${k} differs across screens: ` + JSON.stringify(seen));
    // top-left of the content: the screen edge for the full-width graph, the page column's edge for pages
    const pages = seen.filter((s) => s.scr !== 'explore'); assert.equal(new Set(pages.map((s) => s.x)).size, 1, 'page back links line up: ' + JSON.stringify(seen));
    if (name === 'phone') assert.equal(new Set(seen.map((s) => s.x)).size, 1, 'on a phone they sit in the same spot: ' + JSON.stringify(seen));
    await b.close();
  });
}

// docs/DESIGN.md: every page has a share icon and the same "Sources & credits" footer.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: journey, place and explore all have a share icon; pages and the species sheet share one footer`, async () => {
    const b = await H.launch();
    for (const [scr, hash] of [['place', '#stub&pg=yellowstone'], ['explore', '#stub&e=yellowstone'], ['journey', '#stub']]) {
      const t = await H.open(b, H.MAIN, size, { hash }); const p = t.page;
      if (scr === 'journey') await p.evaluate(() => window.__M.showJourney(window.__M.journeyIds()[0]));
      await p.waitForSelector(scr === 'explore' ? '#pbk' : '.jback', { state: 'visible', timeout: 60000 }); await p.waitForTimeout(1000);
      const r = await p.evaluate(() => { const v = [...document.querySelectorAll('.shbtn')].filter((e) => e.getBoundingClientRect().width > 0); const f = [...document.querySelectorAll('details.srcd summary')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => e.textContent.trim()); return { share: v.length, foot: f }; });
      assert.equal(r.share, 1, `${scr}: exactly one share icon`);
      if (scr !== 'explore') assert.deepEqual(r.foot, ['Sources & credits'], `${scr}: shared footer`);
      assert.deepEqual(t.errors, []); await t.close();
    }
    await b.close();
  });
}
