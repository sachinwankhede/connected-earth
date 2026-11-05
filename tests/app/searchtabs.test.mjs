// iPhone feedback (#443): the pictures of species are in the dropdown and in the Species tab's search results; while a search is on every tab says how many it found
// (Places 12, Species 3, Journeys 0) and the Journeys tab follows the search; "Show them on the map" lands on the Places tab.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const tabs = (p) => p.evaluate(() => [...document.querySelectorAll('#tabs [data-tab], #trow [data-tab]')].filter((b) => b.offsetParent).map((b) => b.textContent.trim()));
const picLoaded = (p, sel) => p.waitForFunction((s) => { const i = document.querySelector(s + ' img'); return !!i && i.complete && i.naturalWidth > 0 && /photos\/species\/.+\.webp/.test(i.src); }, sel, { timeout: 30000 });

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: species rows in the dropdown and in the Species tab search show their picture`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('osprey');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    await picLoaded(p, '#sug .sgr[data-latin="Pandion haliaetus"]');
    await p.keyboard.press('Enter');
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => /species? match/.test(document.getElementById('qnote').textContent) && !document.querySelector('#sptab .sgr[data-g]') && document.querySelector('#sptab .sgl .sgr'), null, { timeout: 60000 });
    await picLoaded(p, '#sptab .sgr[data-latin="Pandion haliaetus"]');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: with a search on, every tab says how many it found, and clearing removes the counts`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    assert.deepEqual((await tabs(p)).slice(0, 2), ['Places', 'Species'], 'no counts without a search');
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'osprey', null, { timeout: 60000 });
    await p.waitForFunction(() => /^Places \d+$/.test(document.querySelector('#tabs [data-tab="places"]').textContent) && /^Species \d+$/.test(document.querySelector('#tabs [data-tab="species"]').textContent), null, { timeout: 30000 });
    const tx = await tabs(p); assert.match(tx[0], /^Places [1-9]\d*$/); assert.match(tx[1], /^Species [1-9]\d*$/);
    if (tx[2]) {   // Journeys is shown: its count is what its tab lists
      assert.match(tx[2], /^Journeys \d+$/);
      await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(500);
      const shown = await p.evaluate(() => [...document.querySelectorAll('#xcards li')].filter((l) => !l.hidden).length);
      assert.equal('Journeys ' + shown, (await tabs(p))[2], 'the count is the journeys listed');
      assert.equal(await p.evaluate(() => window.__M.tab), 'journeys');
    }
    // the same note line, in the same words, on every tab (#449)
    const note = (kind) => p.evaluate(() => { const n = document.getElementById('qnote'); return n.hidden ? null : n.textContent; });
    await p.click('[data-tab="places"]:visible'); await p.waitForTimeout(400);
    assert.match(await note(), /^\d+ places? match(es)? “osprey”$/, 'Places says what it found');
    await p.click('[data-tab="species"]:visible'); await p.waitForTimeout(600);
    assert.match(await note(), /^\d+ species match(es)? “osprey”$/, 'Species says it in the same form');
    if (tx[2]) { await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(400); assert.match(await note(), /^(No|\d+) journeys? match(es)? “osprey”$/, 'Journeys too'); }
    await p.click('[data-tab="places"]:visible');
    await p.click('#qclr'); await p.waitForTimeout(700);
    assert.equal(await note(), null, 'the note goes with the search');
    assert.deepEqual((await tabs(p)).slice(0, 2), ['Places', 'Species'], 'counts go with the search');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a search that finds places but no species still says so on the Species tab (#449)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('sahara'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'sahara', null, { timeout: 60000 });
    await p.waitForFunction(() => { const n = document.getElementById('qnote'); return !n.hidden && /places? match(es)? “sahara”$/.test(n.textContent); }, null, { timeout: 30000 });
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => { const n = document.getElementById('qnote'); return !n.hidden && /species match(es)? “sahara”$/.test(n.textContent) && !document.querySelector('#sptab .sgr[data-g]'); }, null, { timeout: 30000 });
    const list = await p.evaluate(() => ({ note: document.getElementById('qnote').textContent, rows: document.querySelectorAll('#sptab .sgr[data-latin]').length, top: !!document.querySelector('#sptab .sgr[data-g]') }));
    assert.equal(list.top, false, 'the groups are out of the way during a search'); assert.equal(/^No species/.test(list.note), list.rows === 0, 'the note and the list agree: ' + JSON.stringify(list));
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: "Show them on the map" from the Species tab lands on the Places tab`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelectorAll('#sptab .sgr[data-latin]').length > 0, null, { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#sptab .sgr[data-latin]').click());
    await p.waitForFunction(() => document.querySelector('#pview [data-spmap]'), null, { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#pview [data-spmap]').click());
    await p.waitForFunction(() => document.getElementById('pview').hidden, null, { timeout: 30000 });
    assert.equal(await p.evaluate(() => window.__M.tab), 'places');
    assert.equal(await p.evaluate(() => document.getElementById('sptab').hidden), true, 'the Species list is out of the way');
    assert.equal(await p.evaluate(() => document.querySelector('#tabs [data-tab="places"]').getAttribute('aria-pressed')), 'true');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
