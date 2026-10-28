import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';
import { mockPhotos } from './mockphotos.mjs';

describe('place sheet', () => {
  let browser;
  before(async () => { browser = await H.launch(); });
  after(async () => { await browser.close(); });

  for (const [sizeName, size] of Object.entries(H.SIZES)) {
    test(`${sizeName}: a place opens as just the graph; picking a species brings up its sheet; clearing it takes the sheet away`, async () => {
      const t = await H.open(browser, H.MAIN, size, { hash: '#stub&e=npmammothcave' });
      const vis = () => t.page.evaluate(() => { const v = (id) => { const e = document.getElementById(id); return !!e && e.getBoundingClientRect().width > 0 && getComputedStyle(e).display !== 'none'; }; return { sheet: v('psheet'), back: v('pbk'), graph: document.querySelectorAll('.node').length }; });
      await t.page.waitForFunction(() => document.querySelectorAll('.node').length > 3, null, { timeout: 60000 });
      let s = await vis();
      assert.equal(s.sheet, false, 'no sheet or side panel while nothing is selected'); assert.equal(s.back, true, 'a way back is always there');
      assert.match(await t.page.textContent('#pbk'), /^\u2039 Mammoth Cave National Park$/);
      await t.page.click('.node >> nth=0'); await t.page.waitForTimeout(1000);
      s = await vis(); assert.equal(s.sheet, true, 'the species sheet appears'); assert.equal(s.back, true, 'back stays in the same place');
      const picked = await t.page.evaluate(() => ({ lead: document.querySelector('#panel p')?.textContent, sel: document.querySelectorAll('.node.sel,.node.on').length }));
      assert.ok(picked.lead, 'species details shown'); assert.equal(picked.sel, 1, 'exactly one species selected in the graph');
      await t.page.keyboard.press('Escape'); await t.page.waitForTimeout(500);
      s = await vis(); assert.equal(s.sheet, false, 'sheet goes away'); assert.equal(s.back, true);
      assert.equal(await t.page.evaluate(() => !!document.querySelector('.autotag')), false, 'hand-built place has no auto-generated tag');
      assert.deepEqual(t.errors, []);
      await t.close();
    });

    test(`${sizeName}: a species sheet shows what it eats and what eats it as photo cards, details tucked under More, What if last`, async () => {
      const t = await H.open(browser, H.MAIN, size, { hash: '#stub&e=yellowstone' });
      await mockPhotos(t.page);
      await t.page.waitForFunction(() => document.querySelectorAll('.node').length > 3, null, { timeout: 60000 });
      await t.page.evaluate(() => [...document.querySelectorAll('.node')].find((n) => /Elk/.test(n.getAttribute('aria-label'))).dispatchEvent(new MouseEvent('click', { bubbles: true })));
      await t.page.waitForSelector('#panel .prow .pmc', { timeout: 30000 });
      const r = await t.page.evaluate(() => {
        const pn = document.getElementById('panel'), top = (e) => e.getBoundingClientRect().top + pn.scrollTop;
        const heads = [...pn.querySelectorAll('h3')].map((h) => h.textContent.replace(/\s*\(\d+\)/, ''));
        const wi = pn.querySelector('.wi'), more = pn.querySelector('details.more'), last = pn.lastElementChild;
        return { heads, whatIfLast: last === wi, moreClosed: !!more && !more.open, moreBeforeWhatIf: top(more) < top(wi), cards: pn.querySelectorAll('.prow .pmc').length };
      });
      await t.page.waitForFunction(() => document.querySelector('#panel .art.hasph img'), null, { timeout: 30000 });
      const lay = await t.page.evaluate(() => { const a = document.querySelector('#panel .art').getBoundingClientRect(), l = document.querySelector('#panel .latin').getBoundingClientRect(); return { photoLeft: a.right <= l.left, close: !!document.querySelector('.pclose'), found: [...document.querySelectorAll('#panel h3')].some((h) => /^Also found in \d+ other place/.test(h.textContent)) }; });
      assert.ok(lay.photoLeft, 'photo on the left, details on the right'); assert.equal(lay.close, false, 'no close button'); assert.ok(lay.found, 'Also found in is a row of places');
      await t.page.waitForFunction(() => { const c = document.querySelectorAll('#panel .pph[data-eid]'); return c.length > 0 && [...c].every((x) => x.querySelector('img')); }, null, { timeout: 30000 });
      assert.deepEqual(r.heads.slice(0, 2), ['What Elk eats', 'What eats Elk']); assert.ok(r.whatIfLast, 'What if is the last thing'); assert.ok(r.moreClosed && r.moreBeforeWhatIf);
      await t.page.waitForFunction(() => { const c = document.querySelectorAll('#panel .prow .pmc .pph'); return c.length > 0 && [...c].every((x) => x.querySelector('img')); }, null, { timeout: 30000 });
      // tapping a neighbour moves the selection to it
      const before = await t.page.evaluate(() => document.querySelector('#panel h2, #prow .stt').textContent);
      await t.page.evaluate(() => document.querySelectorAll('#panel .prow')[1].querySelector('.pmc').click()); await t.page.waitForTimeout(800);
      const after = await t.page.evaluate(() => document.querySelector('#prow .stt').textContent);
      assert.notEqual(after, before, 'selection moved to the tapped species');
      if (sizeName === 'phone') {
        const h = () => t.page.evaluate(() => Math.round(document.getElementById('psheet').getBoundingClientRect().height));
        const full = await h(); await t.page.click('.pchev'); await t.page.waitForTimeout(700);
        assert.ok((await h()) < 100, 'the chevron collapses the sheet to its top line');
        await t.page.click('#phead'); await t.page.waitForTimeout(700);
        assert.ok((await h()) > full - 5, 'tapping the top line opens it again');
      }
      assert.deepEqual(t.errors, []); await t.close();
    });

    test(`${sizeName}: picking an environment item shows the environment so the selection is visible`, async () => {
      const t = await H.open(browser, H.MAIN, size, { hash: '#stub&pg=yellowstone' });
      await t.page.waitForSelector('#pgraph .pn', { timeout: 60000 });
      const env = await t.page.evaluate(() => { const c = document.querySelector('.prow .pmc[data-pnode]'); return [...document.querySelectorAll('#pview h3')].find((h) => /^Environment/.test(h.textContent)).nextElementSibling.querySelector('[data-pnode]').getAttribute('data-pnode'); });
      await t.page.click(`#pview [data-pnode="${env}"]`); await t.page.waitForTimeout(2500);
      const r = await t.page.evaluate(() => { const n = document.querySelector('.node.sel,.node.on'); const b = n && n.getBoundingClientRect(); return { shown: !!n && b.width > 0, env: document.getElementById('env').getAttribute('aria-pressed'), sheet: document.getElementById('psheet').getBoundingClientRect().width > 0 }; });
      assert.equal(r.env, 'true'); assert.ok(r.shown, 'the selected environment item is on the graph'); assert.ok(r.sheet);
      assert.deepEqual(t.errors, []); await t.close();
    });

    test(`${sizeName}: the graph has no toolbar until it is moved; the environment is always shown; sharing lives on the place page`, async () => {
      const t = await H.open(browser, H.MAIN, size, { hash: '#stub&e=yellowstone' });
      await t.page.waitForFunction(() => document.querySelectorAll('.node').length > 3, null, { timeout: 60000 }); await t.page.waitForTimeout(1500);
      const vis = () => t.page.evaluate(() => { const v = (id) => { const e = document.getElementById(id); return !!e && e.getBoundingClientRect().width > 0 && getComputedStyle(e).display !== 'none'; }; return { env: v('env'), web: v('vt'), more: v('moreb'), share: v('share'), key: v('kbtn'), fit: v('fit'), bar: v('webctl'), cap: v('gcap'), sun: [...document.querySelectorAll('.node')].some((n) => /Sunlight/.test(n.getAttribute('aria-label')) && n.getBoundingClientRect().width > 0) }; });
      let s = await vis();
      assert.deepEqual([s.env, s.web, s.more, s.share, s.key, s.fit, s.bar], [false, false, false, false, false, false, false], 'no buttons on a fresh graph'); assert.ok(s.cap && s.sun, 'caption and environment shown');
      await t.page.mouse.move(size.width / 2, size.height / 2); await t.page.mouse.wheel(0, -500); await t.page.waitForTimeout(800);
      s = await vis(); assert.ok(s.fit, 'Fit appears once the graph has been moved'); await t.page.click('#fit'); await t.page.waitForTimeout(900);
      s = await vis(); assert.equal(s.fit, false, 'and goes away once it is back');
      await t.page.evaluate(() => window.__M.showPlace('yellowstone')); await t.page.waitForSelector('#pgraph .pn', { timeout: 60000 });
      assert.ok(await t.page.evaluate(() => !!document.querySelector('#pview [data-pshare]')), 'place page has Share');
      assert.deepEqual(t.errors, []); await t.close();
    });

    test(`${sizeName}: auto-generated places show no tag (the flag stays in the data)`, async () => {
      const t = await H.open(browser, H.PILOT, size, { hash: '#stub&e=mocastlewood' });
      assert.equal(await t.page.evaluate(() => !!document.querySelector('.autotag')), false);
      assert.ok(await t.page.evaluate(() => !document.getElementById('webview').hidden), 'the place opened');
      assert.deepEqual(t.errors, []);
      await t.close();
    });
  }
});
