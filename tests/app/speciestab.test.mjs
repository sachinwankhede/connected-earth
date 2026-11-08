// The Species tab (#422 step 2): a third tab (Places, Species, Journeys); nothing of it is fetched until it opens; its first screen is the species found in the most places;
// a row opens the species page and Back returns to the tab; Places brings the places list back.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const fetched = (p, re) => p.evaluate((s) => performance.getEntriesByType('resource').some((r) => new RegExp(s).test(r.name)), re.source);

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
    const s = await p.evaluate(() => ({ rows: [...document.querySelectorAll('#sptab .sgr[data-latin]')].map((r) => ({ n: r.querySelector('b').textContent, l: r.querySelector('i').textContent, h: r.getBoundingClientRect().height })), cards: getComputedStyle(document.getElementById('cards')).display, head: document.querySelector('#sptab h3').textContent }));
    assert.equal(s.rows.length, top.length); assert.equal(s.rows[0].n, top[0][1]); assert.equal(s.rows[0].l, 'Species · in ' + top[0][2] + ' places');
    assert.ok(s.rows.every((r) => /^Species · in \d+ places?$/.test(r.l) && r.h >= 44)); assert.equal(s.cards, 'none', 'the places list is out of the way'); assert.equal(s.head, 'Found in the most places');
    await p.locator('#sptab .sgr[data-latin]').first().click({ timeout: 5000 }).catch(() => p.evaluate(() => document.querySelector('#sptab .sgr[data-latin]').click()));
    await p.waitForFunction((n) => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === n, top[0][1], { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ Species');
    await p.evaluate(() => history.back()); await p.waitForTimeout(1000);
    assert.equal(await p.evaluate(() => document.getElementById('sptab').hidden), false, 'Back returns to the Species tab'); assert.equal(await p.evaluate(() => document.querySelectorAll('#sptab .sgr[data-latin]').length), top.length);
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
    assert.deepEqual(heads, ['Found in the most places']);
    const rows = await p.evaluate(() => [...document.querySelectorAll('#regions [data-spg]')].map((r) => ({ k: r.getAttribute('data-spg'), t: r.textContent, y: Math.round(r.getBoundingClientRect().top) })));
    assert.equal(rows.length, groups.length + 1, 'All and one pill per group (#519)'); assert.equal(rows[0].k, ''); assert.equal(rows[1].k, groups[0][0]); assert.ok(rows.every((r) => r.y === rows[0].y), 'one sideways row at the top, like the continents');
    const big = groups.findIndex((g) => g[2] > 250);   // a group with a second page, when the data has one
    const gi = big >= 0 ? big : 0, g = groups[gi];
    await p.evaluate((k) => document.querySelector('#regions [data-spg="' + k + '"]').click(), g[0]);
    await p.waitForFunction(() => document.querySelectorAll('#sptab .sgl .sgr[data-latin]').length > 0, null, { timeout: 60000 });
    const v = await p.evaluate(() => ({ back: document.querySelector('#sptab .jback').textContent.trim(), head: document.querySelector('#sptab h3').textContent, n: document.querySelectorAll('#sptab .sgr[data-latin]').length }));
    assert.equal(await p.evaluate(() => document.querySelector('#regions .chip.on').getAttribute('data-spg')), g[0], 'the picked group is the marked pill');
    assert.equal(v.back, '‹ Species'); assert.equal(v.head, g[1] + ' · ' + g[2]); assert.equal(v.n, Math.min(g[2], 250));
    if (g[2] > 250) {
      await p.evaluate(() => document.querySelector('#sptab [data-more]').click());
      await p.waitForFunction((n) => document.querySelectorAll('#sptab .sgr[data-latin]').length > n, 250, { timeout: 60000 });
    }
    await p.evaluate(() => document.querySelector('#sptab .jback').click());
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 15000 });
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
    await p.waitForFunction(() => /species? match(es)? “osprey”$/.test(document.getElementById('qnote').textContent) && !document.querySelector('#regions [data-spg]') && document.querySelector('#sptab .sgl .sgr'), null, { timeout: 60000 });
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
