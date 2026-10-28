import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  async function start(hash = '#stub') {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash });
    const errors = []; t.page.on('pageerror', (e) => errors.push(String(e)));
    await t.page.waitForTimeout(500);
    return { b, p: t.page, errors };
  }
  const shown = (p) => p.evaluate(() => ({ page: !document.getElementById('pview').hidden, web: !document.getElementById('webview').hidden, map: !document.getElementById('mapview').hidden, journey: !document.getElementById('jview').hidden, hash: location.hash, back: document.getElementById('back').textContent.trim(), sel: (document.querySelector('#svg .node.sel') || {}).textContent || null }));
  const ready = (p) => p.waitForSelector('#pgraph .pn', { timeout: 60000 });

  test(`${name}: a place page has the name first, a calm picture of the web, then the detail below`, async () => {
    const { b, p, errors } = await start('#stub&pg=yellowstone');
    await ready(p);
    const r = await p.evaluate(() => {
      const v = document.getElementById('pview'), g = document.getElementById('pgraph'), pl = g.querySelector('.jplay').getBoundingClientRect(), top = (s) => (v.querySelector(s) || { getBoundingClientRect: () => ({ top: 1e9 }) }).getBoundingClientRect().top;
      const circles = [...g.querySelectorAll('.pn .core')].map((c) => c.getBoundingClientRect());
      const hit = circles.filter((c) => c.right > pl.left && c.left < pl.right && c.bottom > pl.top && c.top < pl.bottom).length;
      const labels = [...g.querySelectorAll('.pn text')].map((t) => t.getBoundingClientRect()), overlap = labels.filter((a, i) => labels.some((c, j) => j > i && a.left < c.right - 1 && a.right > c.left + 1 && a.top < c.bottom - 1 && a.bottom > c.top + 1)).length;
      return { title: v.querySelector('h2').textContent, place: v.querySelector('.jr').textContent, lead: !!v.querySelector('.plead'), order: top('h2') < top('.plead') && top('.plead') < top('#pgraph') && top('#pgraph') < top('h3'), nodes: g.querySelectorAll('.pn').length, heads: [...v.querySelectorAll('h3')].map((h) => h.textContent), chips: v.querySelectorAll('[data-pnode]').length, hit, overlap, over: document.documentElement.scrollWidth - document.documentElement.clientWidth, back: v.querySelector('[data-pback]').textContent.trim(), web: !document.getElementById('webview').hidden, map: !document.getElementById('mapview').hidden };
    });
    assert.equal(r.title, 'Greater Yellowstone'); assert.ok(r.place.length > 5); assert.ok(r.lead); assert.ok(r.order, 'name, then hook, then the web, then detail');
    assert.equal(r.nodes, 30); assert.ok(r.heads[0].startsWith('Top predators') && r.heads.some((h) => /^Journeys through here/.test(h)));
    assert.ok(r.chips >= 30); assert.equal(r.hit, 0, 'the Explore label sits clear of the species'); assert.equal(r.overlap, 0, 'labels do not overlap'); assert.ok(r.over <= 0);
    assert.equal(r.back, '‹ Map'); assert.equal(r.web, false); assert.equal(r.map, false);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: every place gets a page that fits the screen`, async () => {
    const { b, p, errors } = await start('#stub&pg=yellowstone');
    await ready(p);
    const ids = await p.evaluate(() => window.__M.ecoIds());
    const bad = [];
    for (const id of ids.slice(0, 60)) {
      await p.evaluate((i) => window.__M.showPlace(i), id);
      await p.waitForFunction((i) => { const h = document.querySelector('#pview h2'); return h && document.querySelector('#pgraph .pn') && location.hash.includes(i); }, id, { timeout: 30000 }).catch(() => {});
      const r = await p.evaluate(() => { const g = document.getElementById('pgraph'); return { n: g ? g.querySelectorAll('.pn').length : 0, over: document.documentElement.scrollWidth - document.documentElement.clientWidth, h: g ? g.getBoundingClientRect().height : 0 }; });
      if (r.n < 3 || r.over > 0 || r.h < 200) bad.push(id + ' ' + JSON.stringify(r));
    }
    assert.deepEqual(bad, []); assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: map card -> place page -> explore -> back to the page -> back to the map`, async () => {
    const { b, p, errors } = await start();
    if (name === 'phone') { await p.click('#speek'); await p.waitForTimeout(500); }
    await p.click('[data-tab="places"]:visible').catch(() => {});
    await p.evaluate(() => document.querySelector('#cards [data-eco]').scrollIntoView());
    const eco = await p.evaluate(() => document.querySelector('#cards [data-eco]').getAttribute('data-eco'));
    await p.click('#cards [data-eco] >> nth=0'); await ready(p);
    let s = await shown(p); assert.equal(s.page, true); assert.equal(s.web, false); assert.equal(s.map, false); assert.match(s.hash, new RegExp('pg=' + eco));
    const bx = await p.locator('#pgraph').boundingBox(); await p.mouse.click(bx.x + 6, bx.y + 6); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.web, true); assert.equal(s.page, false); assert.equal(s.sel, null, 'empty corner opens the explore view with nothing selected'); assert.equal(s.back, '← Place'); assert.match(s.hash, new RegExp('e=' + eco));
    await p.click('.pclose:visible'); await p.waitForTimeout(600);
    s = await shown(p); assert.equal(s.page, true); assert.equal(s.web, false);
    await p.click('[data-pback]'); await p.waitForTimeout(600);
    s = await shown(p); assert.equal(s.map, true); assert.equal(s.page, false);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: a species in the picture or the list opens the explore view with it selected; journeys and neighbours link on`, async () => {
    const { b, p, errors } = await start('#stub&pg=yellowstone');
    await ready(p);
    await p.click('#pgraph .pn >> nth=0'); await p.waitForTimeout(1500);
    let s = await shown(p); assert.equal(s.web, true); assert.ok(s.sel, 'the tapped species is selected');
    await p.click('.pclose:visible'); await p.waitForTimeout(400); await p.click('.pclose:visible'); await ready(p);
    await p.click('[data-pnode="elk"]'); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.web, true); assert.match(s.sel, /Elk/);
    await p.click('.pclose:visible'); await p.waitForTimeout(400); await p.click('.pclose:visible'); await ready(p);
    await p.click('[data-pjourney]'); await p.waitForTimeout(600);
    s = await shown(p); assert.equal(s.journey, true); assert.equal(s.page, false);
    await p.evaluate(() => window.__M.showPlace('yellowstone')); await ready(p);
    await p.click('[data-ppage] >> nth=0'); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.page, true); assert.ok(!/pg=yellowstone/.test(s.hash), 'a different place');
    assert.deepEqual(errors, []); await b.close();
  });
}
