// #589: recent searches. The last three searches (typed and sent with Enter) and the last three rows opened from the dropdown are kept in this browser only and listed in the dropdown while the box is empty and focused.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

const stored = (p) => p.evaluate(() => JSON.parse(localStorage.getItem('ceRs') || '[]'));
const rows = (p) => p.evaluate(() => [...document.querySelectorAll('#sug .sgr')].map((r) => [r.getAttribute('data-q') || r.getAttribute('data-id') || r.getAttribute('data-latin'), r.querySelector('i') ? r.querySelector('i').textContent : '']));
// #684: a click that never goes through on a fresh page. Wait for the same readiness open() waits for (map style drawn), then click; if it still times out, print one compact line (what is on top of the box, ready state, sheet state) so the CI log shows the cause, because CI cuts the Playwright call log.
const tap = async (p, sel) => {
  await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 }).catch(() => {});
  try { await p.click(sel, { timeout: 30000 }); } catch (e) {
    const d = await p.evaluate((s) => { const el = document.querySelector(s); const r = el && el.getBoundingClientRect(); const top = r && document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      return JSON.stringify({ ready: document.readyState, sheet: window.__M && window.__M.sheetState, box: r && [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], top: top && (top.id || top.className || top.tagName), hash: location.hash, vis: document.visibilityState }); }, sel).catch((x) => 'evaluate failed ' + x);
    throw new Error('Timeout on click ' + sel + ' DIAG ' + d);
  }
};
const send = async (p, text) => { await p.fill('#q', text); await p.keyboard.press('Enter'); await p.waitForFunction((x) => window.__M.searched === x, text.toLowerCase(), { timeout: 60000 }); };

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: a search sent with Enter opens a collapsed sheet so the results show`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    const before = await p.evaluate(() => window.__M.sheetState);
    await send(p, 'bear');
    const after = await p.evaluate(() => window.__M.sheetState);
    if (before === 'min') assert.notEqual(after, 'min', 'the sheet stayed collapsed after the search');
    assert.deepEqual(t.errors, []); await b.close();
  });
  test(`${name}: a recent place row has its picture on a fresh page, before the place was opened again`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('yellowstone');
    await p.waitForSelector('#sug .sgr[data-id]', { timeout: 15000 });
    await p.click('#sug .sgr[data-id]');
    assert.equal((await stored(p))[0].t, 'p');
    // #684 (root cause, from the CI diagnostic: box 0x0, hash '#stub&pg=yellowstone'): the app writes '&pg=<place>' into the address when a place opens, and it can do that after a plain goto('#stub') has reset it, so the reload reopened the place page where the search box is hidden. Wait for the place to be written, then reset the hash with replaceState (fires no hashchange, so nothing writes it back) and reload.
    await p.waitForFunction(() => /pg=yellowstone/.test(location.hash), null, { timeout: 30000 });
    await p.evaluate(() => history.replaceState(null, '', location.pathname + location.search + '#stub')); await p.reload();   // a fresh page: no place picture has been read yet
    await tap(p, '#q');
    await p.waitForSelector('#sug .sgr[data-id] .sgi img', { timeout: 30000 });   // the picture arrives after the list is drawn, and the row is drawn again
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: recent searches are listed under the empty box, newest first, at most three, and a tap runs the search again`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q');
    assert.equal(await p.evaluate(() => document.getElementById('sug').hidden), true, 'nothing to list before the first search');
    for (const w of ['osprey', 'bear', 'elk', 'wolf']) await send(p, w);
    assert.deepEqual((await stored(p)).map((x) => x.q), ['wolf', 'elk', 'bear'], 'three, newest first');
    await p.click('#qclr');   // Clear empties the box and keeps the focus
    await p.waitForFunction(() => !document.getElementById('sug').hidden && document.querySelectorAll('#sug .sgr').length === 3, null, { timeout: 15000 });
    assert.deepEqual(await rows(p), [['wolf', ''], ['elk', ''], ['bear', '']], 'a typed search is one line: its text, no second line');
    assert.equal(await p.evaluate(() => document.querySelector('#sug .sgh').firstChild.textContent), 'Recent', 'one label above the rows');
    assert.equal(await p.evaluate(() => document.querySelectorAll('#sug .sgq .sgo').length), 0, 'no chevron on a typed search (a chevron opens a page)');
    assert.equal(await p.evaluate(() => Math.round(document.querySelector('#sug .sgq').getBoundingClientRect().height) >= 44), true, 'at least 44 px tall');
    await p.click('#sug .sgr[data-q="elk"]');
    await p.waitForFunction(() => window.__M.searched === 'elk', null, { timeout: 60000 });
    assert.equal(await p.inputValue('#q'), 'elk');
    assert.deepEqual((await stored(p)).map((x) => x.q), ['elk', 'wolf', 'bear'], 'a search run again from the list is the newest');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: Clear on the Recent line erases the list, keeps the box focused, and a new search brings one row back (#642)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q');
    for (const w of ['osprey', 'bear']) await send(p, w);
    await p.click('#qclr');   // an empty box shows the Recent list
    await p.waitForSelector('#sug .sgh a', { timeout: 15000 });
    assert.equal(await p.evaluate(() => document.querySelector('#sug .sgh a').textContent), 'Clear');
    assert.equal(await p.evaluate(() => { const r = document.querySelector('#sug .sgh a').getBoundingClientRect(); return r.height >= 44; }), true, 'a 44 px tap area');
    assert.equal(await p.evaluate(() => document.querySelectorAll('#sug .sgh').length), 1, 'the link is on the one Recent line, not a row');
    await p.evaluate(() => document.querySelector('#sug .sgh a').click());
    assert.deepEqual(await stored(p), [], 'the stored list is empty');
    assert.equal(await p.evaluate(() => document.getElementById('sug').hidden), true, 'no label and no rows are left');
    assert.equal(await p.evaluate(() => document.activeElement && document.activeElement.id), 'q', 'the box keeps its focus');
    await send(p, 'elk');
    assert.deepEqual((await stored(p)).map((x) => x.q), ['elk'], 'a new search is remembered again');
    assert.deepEqual(t.errors, []); await b.close();
  });
  test(`${name}: a row opened from the dropdown is remembered as that row`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('osprey');
    await p.waitForSelector('#sug .sgr[data-latin="Pandion haliaetus"]', { timeout: 15000 });
    await p.click('#sug .sgr[data-latin="Pandion haliaetus"]');
    assert.deepEqual((await stored(p)).map((x) => x.t + ':' + x.latin), ['s:Pandion haliaetus']);
    assert.equal((await stored(p))[0].rc, 0);
    assert.deepEqual(t.errors, []); await b.close();
  });
}
