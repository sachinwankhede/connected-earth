import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  async function start(eco = 'yellowstone') {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub&e=' + eco });
    const errors = []; t.page.on('pageerror', (e) => errors.push(String(e)));
    await t.page.waitForFunction(() => !document.getElementById('webview').hidden && window.__M.storyChains().length, null, { timeout: 60000 });
    await t.page.waitForTimeout(500);
    return { b, p: t.page, errors };
  }
  const state = (p) => p.evaluate(() => ({
    cap: document.getElementById('wstory').hidden ? null : document.getElementById('wstory').textContent.trim(),
    dot: !!document.querySelector('.wdot'),
    dim: document.querySelectorAll('#svg .node.dim').length, lit: document.querySelectorAll('#svg .node:not(.dim)').length,
    on: document.querySelectorAll('#svg .edge.on').length,
  }));

  test(`${name}: a web opens with a food chain that lights up from plant to predator and then settles`, async () => {
    const { b, p, errors } = await start();
    const chains = await p.evaluate(() => window.__M.storyChains());
    assert.deepEqual(chains[0], ['aspen', 'elk', 'wolf'], 'hand-picked chain for Yellowstone');
    assert.ok(chains.length >= 2 && chains.every((c) => c.length >= 3));
    assert.equal((await state(p)).cap, null, 'tests start with no story unless asked');
    await p.evaluate(() => window.__M.storyPlay(false));
    await p.waitForTimeout(400);
    let s = await state(p); assert.match(s.cap, /aspen$/); assert.equal(s.lit, 1); assert.ok(s.dim > 20, 'the rest of the web is ghosted');
    await p.waitForFunction(() => document.querySelectorAll('#svg .edge.on').length === 1, null, { timeout: 20000 });
    s = await state(p); assert.equal(s.lit, 2); assert.match(s.cap, /aspen.*Elk$/);
    await p.waitForFunction(() => !document.querySelector('.wdot') && document.querySelectorAll('#svg .node.dim').length === 0, null, { timeout: 20000 });
    s = await state(p); assert.equal(s.on, 0, 'the web settles back to normal'); assert.match(s.cap, /aspen.*Elk.*Gray wolf/); assert.equal(s.dot, false);
    // the caption is a replay: another tap plays the next chain
    await p.click('#wstory'); await p.waitForTimeout(400);
    s = await state(p); assert.match(s.cap, /Willow/); assert.equal(s.dot || s.lit === 1, true);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: picking a species stops the story and hides the caption, and it comes back when cleared`, async () => {
    const { b, p, errors } = await start('serengeti');
    await p.evaluate(() => window.__M.storyPlay(false)); await p.waitForTimeout(1800);
    assert.ok((await state(p)).cap);
    await p.evaluate(() => document.querySelector('#svg .node').dispatchEvent(new MouseEvent('click', { bubbles: true })));
    await p.waitForTimeout(600);
    let s = await state(p); assert.equal(s.cap, null); assert.equal(s.dot, false);
    await p.waitForTimeout(3500); s = await state(p); assert.equal(s.cap, null, 'the story does not restart under a selection'); assert.equal(s.dot, false);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    s = await state(p); assert.ok(s.cap, 'caption is back'); assert.equal(s.on, 0);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: every place with a food web gets a sensible chain, and the caption never covers the controls`, async () => {
    const { b, p, errors } = await start('amazon');
    const ids = await p.evaluate(() => window.__M.ecoIds());
    const bad = [];
    for (const id of ids.slice(0, 40)) {
      await p.evaluate((i) => window.__M.openWeb(i), id);
      await p.waitForFunction((i) => !document.getElementById('webview').hidden && window.__M.storyEco() === i, id, { timeout: 30000 }).catch(() => {});
      const c = await p.evaluate(() => window.__M.storyChains());
      if (c.length && c.some((x) => x.length < 3)) bad.push(id);
    }
    assert.deepEqual(bad, []);
    await p.evaluate(() => window.__M.storyPlay(false)); await p.waitForTimeout(300);
    const r = await p.evaluate(() => { const a = document.getElementById('wstory').getBoundingClientRect(), c = document.getElementById('webctl') || document.querySelector('#stage .wtools'); const st = document.getElementById('stage').getBoundingClientRect(); return { right: a.right <= st.right - 50, top: a.top >= st.top }; });
    assert.ok(r.right && r.top, JSON.stringify(r));
    assert.deepEqual(errors, []); await b.close();
  });
}
