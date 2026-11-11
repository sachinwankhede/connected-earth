// The Species tab (#422 step 2): a third tab (Places, Species, Journeys); nothing of it is fetched until it opens; its first screen is the species found in the most places;
// a row opens the species page and Back returns to the tab; Places brings the places list back.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const fetched = (p, re) => p.evaluate((s) => performance.getEntriesByType('resource').some((r) => new RegExp(s).test(r.name)), re.source);

// click a pill of the row, through the More list when the row holds it back (#534)
const pick = async (p, attr, key) => {
  const i = await p.evaluate(([a, k]) => { if (document.querySelector('#regions [' + a + '="' + k + '"]')) return -1; return window.__M.moreRows.findIndex((r) => r.a[a] === k); }, [attr, key]);
  if (i < 0) { await p.evaluate(([a, k]) => document.querySelector('#regions [' + a + '="' + k + '"]').click(), [attr, key]); return; }
  await p.evaluate(() => document.querySelector('#regions [data-pmore]').click());
  await p.evaluate((n) => document.querySelector('#morelist .morei[data-i="' + n + '"]').click(), i);
};


for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: the Species tab loads on demand, lists the most-found species, a row opens the page and Back returns to the tab`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });   // on a phone the tabs are in the sheet, which starts closed
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    const tabs = await p.evaluate(() => [...document.querySelectorAll('#tabs [data-tab], #trow [data-tab]')].filter((b) => b.offsetParent).map((b) => b.textContent.trim()));
    assert.deepEqual(tabs.slice(0, 2), ['Places', 'Species'], 'tab order: ' + tabs); assert.ok(tabs.length === 2 || tabs[2] === 'Journeys', 'Journeys last when it is shown: ' + tabs);
    assert.equal(await fetched(p, /species-tab/), false, 'nothing of the tab at start-up');
    const top = await p.evaluate(() => fetch('api/species-tab/top.json').then((r) => r.json()));
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#sptab .sgr[data-latin]').length > 0, null, { timeout: 60000 });
    assert.equal(await fetched(p, /species-tab-[0-9a-f]+\.js/), true); assert.equal(await fetched(p, /api\/species-tab\/top\.json/), true);
    const s = await p.evaluate(() => ({ rows: [...document.querySelectorAll('#sptab .sgr[data-latin]')].map((r) => ({ n: r.querySelector('b').textContent, l: r.querySelector('i').textContent, h: r.getBoundingClientRect().height })), cards: getComputedStyle(document.getElementById('cards')).display, head: document.querySelectorAll('#sptab h3').length }));
    assert.equal(s.rows.length, top.length); assert.equal(s.rows[0].n, top[0][1]); assert.equal(s.rows[0].l, 'Species · in ' + top[0][2] + ' places');
    assert.ok(s.rows.every((r) => /^Species · in \d+ places?$/.test(r.l) && r.h >= 44)); assert.equal(s.cards, 'none', 'the places list is out of the way'); assert.equal(s.head, 0, 'no heading line (#534)');
    await p.locator('#sptab .sgr[data-latin]').first().click({ timeout: 5000 }).catch(() => p.evaluate(() => document.querySelector('#sptab .sgr[data-latin]').click()));
    await p.waitForFunction((n) => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === n, top[0][1], { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ Species');
    await p.evaluate(() => history.back()); await p.waitForTimeout(1000);
    assert.equal(await p.evaluate(() => document.getElementById('sptab').hidden), false, 'Back returns to the Species tab'); assert.equal(await p.evaluate(() => document.querySelectorAll('#sptab .sgr[data-latin]').length), top.length);
    assert.ok(await p.evaluate(() => document.querySelectorAll('#regions [data-spg]').length > 0), 'the group pills are still there after Back from a species page (#592)');
    await p.evaluate(() => window.dispatchEvent(new HashChangeEvent('hashchange'))); await p.waitForTimeout(500);   // what a return to the app does: the address is applied again and the list redrawn
    assert.ok(await p.evaluate(() => document.querySelectorAll('#regions [data-spg]').length > 0), 'a redraw of the places list does not blank the Species pills (#592)');
    await p.click('[data-tab="places"]:visible'); await p.waitForTimeout(500);
    assert.equal(await p.evaluate(() => document.getElementById('sptab').hidden), true); assert.notEqual(await p.evaluate(() => getComputedStyle(document.getElementById('cards')).display), 'none', 'the places list is back');
    assert.deepEqual(t.errors, []); await b.close();
  });
}

// #422 step 3: below the most-found species the groups are listed; a group opens its own list with "‹ Species" at the top, 250 rows at a time with "Show N more".
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: the Species tab lists groups; a group opens, pages with Show more, and ‹ Species returns`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    const groups = await p.evaluate(() => fetch('api/species-tab/groups.json').then((r) => r.json()));
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    const heads = await p.evaluate(() => [...document.querySelectorAll('#sptab h3')].map((h) => h.textContent));
    assert.deepEqual(heads, [], 'no heading line: the pills carry the names and counts (#534)');
    const rows = await p.evaluate(() => [...document.querySelectorAll('#regions [data-spg]')].map((r) => ({ k: r.getAttribute('data-spg'), t: r.textContent, y: Math.round(r.getBoundingClientRect().top) })));
    assert.equal(rows.length, Math.min(groups.length, 6) + 1, 'All and the biggest groups, at most 8 pills with More (#534)'); assert.equal(rows[0].k, ''); assert.equal(rows[1].k, groups[0][0]); assert.ok(rows.every((r) => r.y === rows[0].y), 'one sideways row at the top, like the continents');
    const big = groups.findIndex((g) => g[2] > 250);   // a group with a second page, when the data has one
    const gi = big >= 0 ? big : 0, g = groups[gi];
    await pick(p, 'data-spg', g[0]);
    await p.waitForFunction(() => document.querySelectorAll('#sptab .sgl .sgr[data-latin]').length > 0, null, { timeout: 60000 });
    const v = await p.evaluate(() => ({ back: document.querySelector('#sptab .jback') ? 'back' : 'none', head: document.querySelector('#regions .chip.on').textContent, h3: document.querySelectorAll('#sptab h3').length, n: document.querySelectorAll('#sptab .sgr[data-latin]').length }));
    assert.equal(await p.evaluate(() => document.querySelector('#regions .chip.on').getAttribute('data-spg')), g[0], 'the picked group is the marked pill');
    assert.equal(v.back, 'none', 'the All pill is the way back, no second link (#526)'); assert.equal(v.h3, 0, 'no heading line'); assert.equal(v.head.replace(/^All /, ''), g[1] + ' ' + g[2], 'the selected pill says the name and the count (All <group> when it has orders)'); assert.equal(v.n, Math.min(g[2], 250));
    if (g[2] > 250) {
      await p.evaluate(() => document.querySelector('#sptab [data-more]').click());
      await p.waitForFunction((n) => document.querySelectorAll('#sptab .sgr[data-latin]').length > n, 250, { timeout: 60000 });
    }
    await p.evaluate(() => document.querySelector('#regions [data-spg=""],#regions [data-spu]').click());   // inside a group with orders the way back is ‹ Groups (#519 level 2)
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0 && !document.querySelector('#regions [data-spu]'), null, { timeout: 15000 });
    assert.deepEqual(t.errors, []); await b.close();
  });
  // #519 level 2: a group with orders turns the one row into its orders (‹ Groups, All <group>, then each order with its count); an order lists only its species; ‹ Groups goes back.
  test(`${name}: the Species pills go group, then order, and back (#519)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    const groups = await p.evaluate(() => fetch('api/species-tab/groups.json').then((r) => r.json()));
    const g = groups.find((x) => x[4] > 1); assert.ok(g, 'the data has a group with orders');
    const orders = await p.evaluate((k) => fetch('api/species-tab/o-' + k + '.json').then((r) => r.json()), g[0]);
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    await pick(p, 'data-spg', g[0]);
    await p.waitForFunction(() => document.querySelector('#regions [data-spo]'), null, { timeout: 60000 });
    const row = await p.evaluate(() => ({ lbl: document.querySelector('#regions .lbl').textContent, k: [...document.querySelectorAll('#regions .chip')].map((c) => c.getAttribute('data-spu') ? 'up' : c.getAttribute('data-spo') || 'all'), on: document.querySelector('#regions .chip.on').textContent, ys: [...document.querySelectorAll('#regions .chip')].map((c) => Math.round(c.getBoundingClientRect().top)) }));
    assert.equal(row.lbl, 'Orders'); assert.deepEqual(row.k, ['up', 'all'].concat(orders.length > 6 ? orders.slice(0, 5).map((o) => o[0]).concat(['all']) : orders.map((o) => o[0]))); assert.ok(row.on.startsWith('All '), 'All of the group is marked first'); assert.ok(row.ys.every((y) => y === row.ys[0]), 'still one sideways row');
    const wide = () => p.evaluate(() => { const sb = document.getElementById('sbody'); return sb.scrollWidth - sb.clientWidth; });
    if (size.width < 700) assert.ok((await wide()) <= 1, 'the open group does not pan sideways: ' + (await wide()) + ' px too wide');   // owner, 10 Nov
    const o = orders[0];
    await p.evaluate((k) => document.querySelector('#regions [data-spo="' + k + '"]').click(), o[0]);
    await p.waitForFunction((n) => document.querySelector('#regions .chip.on[data-spo]') && document.querySelectorAll('#sptab .sgr[data-latin]').length === n, Math.min(o[2], 250), { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelectorAll('#sptab h3').length), 0, 'no heading line');
    assert.equal(await p.evaluate(() => document.querySelector('#regions .chip.on').getAttribute('data-spo')), o[0], 'the picked order is the marked pill');
    if (orders.length > 3) {   // a pick comes first after the back pill and All, visible or not (#534)
      const o3 = orders[Math.min(orders.length - 1, 3)];
      await pick(p, 'data-spo', o3[0]);
      await p.waitForFunction((k) => document.querySelector('#regions .chip.on[data-spo="' + k + '"]'), o3[0], { timeout: 60000 });
      const c = await p.evaluate(() => [...document.querySelectorAll('#regions .chip')].map((x) => ({ k: x.getAttribute('data-spu') ? 'up' : x.getAttribute('data-spg') !== null ? 'all' : x.getAttribute('data-spo'), on: x.classList.contains('on') })));
      assert.deepEqual(c.slice(0, 3).map((x) => x.k), ['up', 'all', o3[0]], 'the pick is the first pill after the back pill and All'); assert.equal(c[2].on, true); assert.ok(c.length <= 8);
    }
    await p.evaluate((k) => document.querySelector('#regions [data-spg="' + k + '"]').click(), g[0]);   // All <group>: the whole group again
    await p.waitForFunction((n) => document.querySelector('#regions .chip.on[data-spg]') && document.querySelectorAll('#sptab .sgr[data-latin]').length === n, Math.min(g[2], 250), { timeout: 30000 });
    await p.evaluate(() => document.querySelector('#regions [data-spu]').click());
    await p.waitForFunction(() => document.querySelector('#regions [data-spg=""].on') && !document.querySelector('#regions [data-spu]'), null, { timeout: 15000 });
    assert.deepEqual(t.errors, []); await b.close();
  });
}

// #422 step 4: on the Species tab the search box looks for species only -- in the tab's list and in the dropdown -- and Clear brings the tab back.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: on the Species tab the box finds species only and Clear returns to the tab`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('osprey');
    await p.waitForFunction(() => /species? match(es)? “osprey”$/.test(document.getElementById('qnote').textContent) && !document.querySelector('#regions [data-spg]') && document.querySelector('#sptab .sgl .sgr[data-latin="Pandion haliaetus"]'), null, { timeout: 60000 });
    const r = await p.evaluate(() => ({ head: document.getElementById('qnote').textContent, rows: [...document.querySelectorAll('#sptab .sgr')].map((x) => ({ latin: x.getAttribute('data-latin'), g: x.hasAttribute('data-g'), l: x.querySelector('i').textContent })), places: document.querySelectorAll('#sptab .sgr[data-id]').length }));
    assert.match(r.head, /^\d+ species match(es)? “osprey”$/); assert.ok(r.rows.length > 0 && r.rows.every((x) => x.latin && !x.g && /^Species · in \d+ places?$/.test(x.l)), 'only species rows');
    assert.equal(r.rows[0].latin, 'Pandion haliaetus', 'the osprey first'); assert.equal(r.places, 0);
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    const sug = await p.evaluate(() => [...document.querySelectorAll('#sug .sgr')].map((x) => x.getAttribute('data-id') ? 'place' : 'species'));
    assert.ok(sug.length > 0 && sug.every((x) => x === 'species'), 'the dropdown has species only: ' + sug);
    await p.locator('#sptab .sgr').first().click({ timeout: 5000 }).catch(() => p.evaluate(() => document.querySelector('#sptab .sgr').click()));
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    await p.evaluate(() => history.back()); await p.waitForTimeout(1000);
    assert.equal(await p.evaluate(() => document.getElementById('sptab').hidden), false, 'Back returns to the Species tab');
    await p.click('#q', { clickCount: 3 }).catch(() => {}); await p.keyboard.press('Control+A'); await p.keyboard.type('zzqxv');
    await p.waitForFunction(() => /^No species match/.test(document.getElementById('qnote').textContent) && document.querySelector('#sptab [data-clr]'), null, { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#sptab [data-clr]').click());
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 15000 });
    assert.equal(await p.evaluate(() => document.getElementById('q').value), '', 'Clear empties the box');
    assert.deepEqual(t.errors, []); await b.close();
  });
}

// #533a: the Places region and the habitat filter chips do not follow you to the Species tab; the tab shows one row of pills (its groups); Places keeps its region.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: the Places region does not carry over to the Species tab, which shows one row of pills`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-go="continent"][data-a="North America"]', { state: 'attached', timeout: 60000 });
    await p.evaluate(() => document.querySelector('[data-go="continent"][data-a="North America"]').click()); await p.waitForTimeout(1500);
    const was = await p.evaluate(() => document.getElementById('srow').textContent.trim());
    assert.match(was, /North America/, 'the region is on the Places tab: ' + was);
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    const s = await p.evaluate(() => ({ title: document.getElementById('srow').textContent.trim(), trail: document.querySelectorAll('#srow .sbk').length, stats: getComputedStyle(document.getElementById('stats')).display,
      kinds: getComputedStyle(document.getElementById('kinds')).display, goChips: document.querySelectorAll('#regions [data-go]').length, rows: new Set([...document.querySelectorAll('#regions .chip')].map((c) => Math.round(c.getBoundingClientRect().top))).size }));
    assert.equal(s.trail, 0, 'no region trail: ' + s.title); assert.ok(!/North America/.test(s.title), s.title); assert.equal(s.stats, 'none'); assert.equal(s.kinds, 'none'); assert.equal(s.goChips, 0); assert.equal(s.rows, 1, 'one row of pills');
    await p.click('[data-tab="places"]:visible'); await p.waitForTimeout(800);
    assert.match(await p.evaluate(() => document.getElementById('srow').textContent.trim()), /North America/, 'Places keeps its region');
    assert.notEqual(await p.evaluate(() => getComputedStyle(document.getElementById('stats')).display), 'none');
    assert.deepEqual(t.errors, []); await b.close();
  });
}

// #534: a row holds at most 8 pills; the rest are under "More", a vertical list; picking one closes it and shows it as the selected pill.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: at most 8 pills, the rest under More; the pick becomes the selected pill (#534)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    const groups = await p.evaluate(() => fetch('api/species-tab/groups.json').then((r) => r.json()));
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    assert.equal(groups.length, 8, 'eight groups (#534)');
    const row = () => p.evaluate(() => ({ n: document.querySelectorAll('#regions .chip').length, more: !!document.querySelector('#regions [data-pmore]'), list: document.getElementById('morelist') && !document.getElementById('morelist').hidden }));
    assert.deepEqual(await row(), { n: 8, more: true, list: null }, 'All, 6 groups and More');
    await p.evaluate(() => document.querySelector('#regions [data-pmore]').click());
    const rest = await p.evaluate(() => [...document.querySelectorAll('#morelist .morei')].map((r) => ({ t: r.querySelector('b').textContent, on: r.classList.contains('on'), circle: !!r.querySelector('.rd'), chevron: !!r.querySelector('svg, .chev') })));
    assert.deepEqual(rest.map((r) => r.t), ['All'].concat(groups.map((g) => g[1])), 'the list holds every choice of the row, All first, so nothing seems missing');
    assert.deepEqual(rest.map((r) => r.on), [true].concat(groups.map(() => false)), 'the current choice (All) is marked');
    assert.ok(rest.every((r) => r.circle && !r.chevron), 'a circle on each row says pick one; a chevron means a page opens');
    assert.equal(await p.evaluate(() => document.querySelector('#regions [data-pmore]').getAttribute('aria-expanded')), 'true');
    await p.evaluate(() => document.querySelectorAll('#morelist .morei')[7].click());
    await p.waitForFunction((k) => document.querySelector('#regions .chip.on[data-spg="' + k + '"]') || document.querySelector('#regions [data-spo]'), groups[6][0], { timeout: 60000 });
    const shape = await p.evaluate(() => { const c = [...document.querySelectorAll('#regions .chip')]; return { more: c[c.length - 1].hasAttribute('data-pmore') && c[c.length - 1].textContent.trim(), chevrons: c.filter((x) => x.querySelector('.cv')).length }; });
    assert.deepEqual(shape, { more: 'More', chevrons: 1 }, 'More stays the last pill, reads More and is the only pill with a chevron (#534)');
    const after = await row(); assert.ok(after.n <= 8 && after.list !== true, 'still at most 8 pills, the ‹ back pill counts too, and the list is closed');
    const cp = await p.evaluate(() => { const it = []; for (let i = 0; i < 10; i++) it.push({ k: 'k' + i, a: { 'data-x': 'k' + i }, t: 'T' + i }); return [window.__M.capPills('', it, 'k8', 1), window.__M.capPills('', it.slice(0, 4), 'k2', 1), window.__M.capPills('', it, null, 1)]; });
    assert.ok(cp[0].indexOf('>T8') < cp[0].indexOf('>T0') && !cp[0].includes('>T7'), 'a hidden pick is first, and the last pill moves to More'); assert.ok(cp[1].indexOf('>T2') < cp[1].indexOf('>T0'), 'a visible pick is first too, on a row with no More'); assert.ok(cp[2].indexOf('>T0') < cp[2].indexOf('>T1'), 'no pick, natural order');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
