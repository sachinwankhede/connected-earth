import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';
import { mockPhotos } from './mockphotos.mjs';

const leave = (p) => p.click('#pbk:visible, #back:visible');
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
      return { title: v.querySelector('h2').textContent, place: v.querySelector('.jr').textContent, lead: !!v.querySelector('.pstory'), order: top('h2') < top('#pgraph') && top('#pgraph') < top('.pstory') && top('.pstory') < top('h3'), nodes: g.querySelectorAll('.pn').length, heads: [...v.querySelectorAll('h3')].map((h) => h.textContent), chips: v.querySelectorAll('[data-pnode]').length, hit, overlap, over: document.documentElement.scrollWidth - document.documentElement.clientWidth, back: v.querySelector('[data-pback]').textContent.trim(), web: !document.getElementById('webview').hidden, map: !document.getElementById('mapview').hidden };
    });
    assert.equal(r.title, 'Greater Yellowstone'); assert.ok(r.place.length > 5); assert.ok(r.lead); assert.ok(r.order, 'name, then hook, then the web, then detail');
    assert.equal(r.nodes, 30); const ix = ['Top predators', 'Hunters', 'Plant-eaters', 'Plants'].map((x) => r.heads.findIndex((h) => h.startsWith(x))); assert.ok(ix.every((v, i) => v >= 0 && (i === 0 || v === ix[i - 1] + 1)), 'four rows by level in order: ' + r.heads);
    assert.ok(r.heads.includes('Who feeds whom') && r.heads.includes('Journeys through here') && r.heads.includes('Shares species with'));
    assert.ok(r.chips >= 30); assert.equal(r.hit, 0, 'the Explore label sits clear of the species'); assert.equal(r.overlap, 0, 'labels do not overlap'); assert.ok(r.over <= 0);
    assert.equal(r.back, '‹ Places'); assert.equal(r.web, false); assert.equal(r.map, false);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: species show their photos in the picture, the cards and the chains, and fall back to icons without them`, async () => {
    const { b, p, errors } = await start();
    // no photos available: icons stay, nothing breaks
    await p.evaluate(() => window.__M.showPlace('yellowstone')); await ready(p); await p.waitForTimeout(1500);
    let r = await p.evaluate(() => ({ img: document.querySelectorAll('#pgraph image').length, gl: [...document.querySelectorAll('#pgraph .pn .gl')].filter((g) => g.getBoundingClientRect().width > 0).length }));
    assert.equal(r.img, 0); assert.ok(r.gl >= 25, 'icons shown');
    // photos available
    await mockPhotos(p);
    await p.evaluate(() => window.__M.showPlace('serengeti')); await ready(p);
    await p.waitForFunction(() => document.querySelectorAll('#pgraph image').length >= 15, null, { timeout: 30000 });
    await p.waitForFunction(() => document.querySelectorAll('.prow .pmc:not(.ppc) .pph img').length >= document.querySelectorAll('.prow .pmc:not(.ppc)').length, null, { timeout: 30000 });
    r = await p.evaluate(() => {
      const v = document.getElementById('pview'), g = v.querySelector('#pgraph');
      const rows = [...v.querySelectorAll('.prow')].map((x) => ({ n: x.querySelectorAll('.pmc').length, scroll: x.scrollWidth > x.clientWidth || x.querySelectorAll('.pmc').length < 6, h: Math.round(x.getBoundingClientRect().height) }));
      return { all: g.querySelectorAll('.pn').length, ph: g.querySelectorAll('.pn.ph').length, species: v.querySelectorAll('.prow .pmc:not(.ppc)').length, withImg: v.querySelectorAll('.prow .pmc:not(.ppc) .pph img').length, rows, desc: v.querySelectorAll('.pd').length, boxes: v.querySelectorAll('.pstats').length, places: v.querySelectorAll('.ppc').length, placeImgs: v.querySelectorAll('.ppc .pph img').length, badges: [...v.querySelectorAll('.pbadge')].map((x) => x.textContent), chainImgs: v.querySelectorAll('.pchain .pph img').length, chainNodes: v.querySelectorAll('.pchain .pcn').length, all2: v.querySelectorAll('details.srcd summary').length, over: document.documentElement.scrollWidth - document.documentElement.clientWidth, glHidden: [...g.querySelectorAll('.pn.ph .gl')].every((x) => getComputedStyle(x).display === 'none'), card: Math.round(v.querySelector('.pmc').getBoundingClientRect().width) };
    });
    assert.equal(r.ph, r.all, 'every species with a photo shows it in the picture'); assert.ok(r.glHidden, 'a photo replaces the icon');
    assert.ok(r.species >= r.all, 'every species has a card in its level row'); assert.equal(r.withImg, r.species, 'every card, environment items included, shows its photo');
    assert.equal(r.desc, 0, 'no descriptions on the small cards'); assert.equal(r.boxes, 0, 'no plain stat boxes'); assert.ok(r.card <= 110, 'small cards: ' + r.card);
    assert.ok(r.places >= 3 && r.placeImgs === r.places, 'places that share species show their photos'); assert.ok(r.badges.includes('Shares the most') && r.badges.includes('Most connected'));
    assert.ok(r.chainNodes >= 3 && r.chainImgs === r.chainNodes); assert.ok(r.over <= 0);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: places with a story show it under the picture with why it matters, others show neither; environment items get photos`, async () => {
    const { b, p, errors } = await start();
    await mockPhotos(p);
    await p.evaluate(() => window.__M.showPlace('yellowstone')); await ready(p);
    await p.waitForFunction(() => { const c = document.querySelectorAll('.prow .pmc:not(.ppc) .pph'); return c.length > 0 && [...c].every((x) => x.querySelector('img')); }, null, { timeout: 60000 });
    let r = await p.evaluate(() => {
      const v = document.getElementById('pview'), h = [...v.querySelectorAll('h3')].map((x) => x.textContent), top = (el) => el.getBoundingClientRect().top;
      const st = v.querySelector('.pstory'), wm = v.querySelector('.jwhy'), g = v.querySelector('#pgraph'), first = v.querySelector('.prow');
      const env = [...v.querySelectorAll('h3')].find((x) => /^Environment/.test(x.textContent)).nextElementSibling;
      return { has: !!st && !!wm, order: st && wm && top(g) < top(st) && top(st) < top(wm) && top(wm) < top(first), len: st ? st.textContent.length : 0, matters: wm ? wm.textContent.length : 0, envCards: env.querySelectorAll('.pmc').length, envImgs: env.querySelectorAll('.pph img').length };
    });
    assert.ok(r.has && r.order, 'the story and why it matters sit between the picture and the species rows'); assert.ok(r.len > 120 && r.matters > 80);
    assert.ok(r.envCards >= 2 && r.envImgs === r.envCards, 'environment items show photos: ' + JSON.stringify(r));
    // a place without a story has neither section
    const none = await p.evaluate(() => window.__M.ecoIds().filter((i) => !['yellowstone', 'serengeti', 'amazon', 'everglades', 'galapagos'].includes(i))[0]);
    await p.evaluate((i) => window.__M.showPlace(i), none); await ready(p);
    r = await p.evaluate(() => { const v = document.getElementById('pview'); return { why: !!v.querySelector('.jwhy'), story: /The story\./.test(v.textContent) }; });
    assert.ok(!r.why && !r.story, 'no empty story sections');
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
    const nm = (await p.textContent('#pview h2')).trim(); const bx = await p.locator('#pgraph').boundingBox(); await p.mouse.click(bx.x + 6, bx.y + 6); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.web, true); assert.equal(s.page, false); assert.equal(s.sel, null, 'empty corner opens the explore view with nothing selected'); assert.equal(s.back.replace(/^\S+\s*/, ''), nm, 'back names the place'); assert.match(s.hash, new RegExp('e=' + eco));
    // refreshing the explore view keeps the same back link, and it still goes to the place page
    await p.reload(); await p.waitForSelector('#pbk', { state: 'visible', timeout: 60000 }); await p.waitForTimeout(1500);
    assert.equal((await p.textContent('#pbk')).replace(/^\S+\s*/, '').trim(), nm, 'same label after a refresh');
    await leave(p); await p.waitForTimeout(600);
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
    await p.keyboard.press('Escape'); await p.waitForTimeout(400); await leave(p); await ready(p);
    await p.click('[data-pnode="elk"]'); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.web, true); assert.match(s.sel, /Elk/);
    await p.keyboard.press('Escape'); await p.waitForTimeout(400); await leave(p); await ready(p);
    await p.click('[data-pjourney]'); await p.waitForTimeout(600);
    s = await shown(p); assert.equal(s.journey, true); assert.equal(s.page, false);
    await p.evaluate(() => window.__M.showPlace('yellowstone')); await ready(p);
    await p.click('[data-ppage] >> nth=0'); await p.waitForTimeout(1500);
    s = await shown(p); assert.equal(s.page, true); assert.ok(!/pg=yellowstone/.test(s.hash), 'a different place');
    assert.deepEqual(errors, []); await b.close();
  });
}
