// #589: recent searches. The last three searches (typed and sent with Enter) and the last three rows opened from the dropdown are kept in this browser only and listed in the dropdown while the box is empty and focused.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const stored = (p) => p.evaluate(() => JSON.parse(localStorage.getItem('ceRs') || '[]'));
const rows = (p) => p.evaluate(() => [...document.querySelectorAll('#sug .sgr')].map((r) => [r.getAttribute('data-q') || r.getAttribute('data-id') || r.getAttribute('data-latin'), r.querySelector('i') ? r.querySelector('i').textContent : '']));
const send = async (p, text) => { await p.fill('#q', text); await p.keyboard.press('Enter'); await p.waitForFunction((x) => window.__M.searched === x, text.toLowerCase(), { timeout: 60000 }); };

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: a recent place row has its picture on a fresh page, before the place was opened again`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('yellowstone');
    await p.waitForSelector('#sug .sgr[data-id]', { timeout: 15000 });
    await p.click('#sug .sgr[data-id]');
    assert.equal((await stored(p))[0].t, 'p');
    await p.goto(p.url().split('#')[0] + '#stub'); await p.reload();   // a fresh page: no place picture has been read yet
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q');
    await p.waitForSelector('#sug .sgr[data-id] .sgi img', { timeout: 30000 });   // the picture arrives after the list is drawn, and the row is drawn again
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: recent searches are listed under the empty box, newest first, at most three, and a tap runs the search again`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q');
    assert.equal(await p.evaluate(() => document.getElementById('sug').hidden), true, 'nothing to list before the first search');
    for (const w of ['osprey', 'bear', 'elk', 'wolf']) await send(p, w);
    assert.deepEqual((await stored(p)).map((x) => x.q), ['wolf', 'elk', 'bear'], 'three, newest first');
    await p.click('#qclr');   // Clear empties the box and keeps the focus
    await p.waitForFunction(() => !document.getElementById('sug').hidden && document.querySelectorAll('#sug .sgr').length === 3, null, { timeout: 15000 });
    assert.deepEqual(await rows(p), [['wolf', ''], ['elk', ''], ['bear', '']], 'a typed search is one line: its text, no second line');
    assert.equal(await p.evaluate(() => document.querySelector('#sug .sgh').textContent), 'Recent', 'one label above the rows');
    assert.equal(await p.evaluate(() => document.querySelectorAll('#sug .sgq .sgo').length), 0, 'no chevron on a typed search (a chevron opens a page)');
    assert.equal(await p.evaluate(() => Math.round(document.querySelector('#sug .sgq').getBoundingClientRect().height) >= 44), true, 'at least 44 px tall');
    await p.click('#sug .sgr[data-q="elk"]');
    await p.waitForFunction(() => window.__M.searched === 'elk', null, { timeout: 60000 });
    assert.equal(await p.inputValue('#q'), 'elk');
    assert.deepEqual((await stored(p)).map((x) => x.q), ['elk', 'wolf', 'bear'], 'a search run again from the list is the newest');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a row opened from the dropdown is remembered as that row`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('osprey');
    await p.waitForSelector('#sug .sgr[data-latin="Pandion haliaetus"]', { timeout: 15000 });
    await p.click('#sug .sgr[data-latin="Pandion haliaetus"]');
    assert.deepEqual((await stored(p)).map((x) => x.t + ':' + x.latin), ['s:Pandion haliaetus']);
    assert.equal((await stored(p))[0].rc, 0);
    assert.deepEqual(t.errors, []); await b.close();
  });
}
