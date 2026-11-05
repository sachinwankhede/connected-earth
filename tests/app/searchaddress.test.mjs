// A search is part of the address (#412): `s=<text>` is written as you type, a reload or a shared link brings it back, a place opened from a search is a step of its own,
// and Back goes place -> search list -> no search. Text with spaces and & survives. The region view and a search can be in one address.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const same = (a, b, msg) => assert.deepEqual(a, b, msg + ' -- got ' + JSON.stringify(a) + ' expected ' + JSON.stringify(b));
const names = (p) => p.evaluate(() => [...document.querySelectorAll('#cards li:not([hidden]) h2')].map((h) => h.textContent));
const state = (p) => p.evaluate(() => ({ box: document.getElementById('q').value, hash: decodeURIComponent(location.hash), page: !document.getElementById('pview').hidden, map: !document.getElementById('mapview').hidden, clr: !document.getElementById('qclr').hidden }));
const answered = (p, q) => p.waitForFunction((x) => window.__M && window.__M.searched === x, q, { timeout: 60000 });   // the index has answered q and the list has been drawn for it
const search = async (p, text) => {
  await p.click('#q'); await p.keyboard.type(text); await p.keyboard.press('Enter');
  await answered(p, text.toLowerCase());
  await p.waitForFunction(() => document.querySelector('#cards [data-eco]'), null, { timeout: 30000 });
};
const openFirst = async (p) => {
  const id = await p.evaluate(() => document.querySelector('#cards [data-eco]').getAttribute('data-eco'));
  await p.evaluate(() => document.querySelector('#cards [data-eco]').click());
  await p.waitForFunction(() => !document.getElementById('pview').hidden && document.querySelector('#pview h2'), null, { timeout: 30000 });
  return id;
};
const back = async (p) => { await p.evaluate(() => history.back()); await p.waitForTimeout(700); };

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: typing writes s= in the address, a reload brings the same list back, Clear removes it`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await search(p, 'elk');
    let s = await state(p);
    assert.match(s.hash, /(^|&)s=elk($|&)/, 'the search is in the address');
    const before = await names(p);
    assert.ok(before.length > 0, 'something matches elk');
    await p.reload(); await answered(p, 'elk');
    s = await state(p);
    assert.equal(s.box, 'elk', 'the box has the text again after a reload'); assert.equal(s.clr, true, 'and its Clear link');
    same(await names(p), before, 'the same list after a reload');
    await p.click('#qclr'); await p.waitForTimeout(400);
    s = await state(p); assert.equal(s.box, ''); assert.doesNotMatch(s.hash, /(^|&)s=/, 'no search left in the address');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a place opened from a search keeps the search; Back returns to the list, and once more clears the search`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await search(p, 'elk');
    const before = await names(p);
    const id = await openFirst(p);
    let s = await state(p);
    assert.match(s.hash, new RegExp('(^|&)s=elk&pg=' + id + '$'), 'the address has the search and the place');
    // reload on the place: the place and the search are both there, and the link back goes to the same list
    await p.reload(); await answered(p, 'elk'); await p.waitForFunction(() => !document.getElementById('pview').hidden && document.querySelector('#pview h2'), null, { timeout: 60000 });
    s = await state(p); assert.equal(s.page, true); assert.equal(s.box, 'elk');
    await p.click('[data-pback]'); await p.waitForTimeout(700);
    s = await state(p); assert.equal(s.map, true, 'the list is back'); assert.equal(s.box, 'elk', 'with the search');
    assert.doesNotMatch(s.hash, /pg=/); assert.match(s.hash, /(^|&)s=elk$/);
    same(await names(p), before, 'the same list as before the place');
    // the browser's Back from a place: open one again, then Back
    await openFirst(p);
    await back(p);
    s = await state(p); assert.equal(s.page, false, 'Back closes the place'); assert.equal(s.map, true); assert.equal(s.box, 'elk', 'and keeps the search');
    same(await names(p), before, 'the same list');
    // Back again: the search is cleared before leaving
    await back(p);
    s = await state(p); assert.equal(s.box, '', 'Back from the search list clears the text'); assert.doesNotMatch(s.hash, /(^|&)s=/);
    assert.equal(s.clr, false);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a shared link with a search opens it, also with a region and with special characters`, async () => {
    let b = await H.launch(); let t = await H.open(b, H.MAIN, size, { hash: '#stub&s=elk' }); let p = t.page;
    await answered(p, 'elk');
    let s = await state(p);
    assert.equal(s.box, 'elk'); assert.equal(s.clr, true); assert.equal(s.map, true);
    assert.ok((await names(p)).length > 0, 'the list is filtered');
    assert.deepEqual(t.errors, []); await b.close();

    b = await H.launch(); t = await H.open(b, H.MAIN, size, { hash: '#stub&s=elk&r=continent:North%20America' }); p = t.page;
    await answered(p, 'elk');
    s = await state(p);
    assert.equal(s.box, 'elk', 'the search and the region together');
    assert.match(s.hash, /(^|&)s=elk&r=continent:North America$/, 'both stay in the address');
    assert.deepEqual(t.errors, []); await b.close();

    b = await H.launch(); t = await H.open(b, H.MAIN, size, { hash: '#stub' }); p = t.page;
    await p.click('#q'); await p.keyboard.type('a & b 100%'); await p.keyboard.press('Enter'); await answered(p, 'a & b 100%');
    await p.reload(); await answered(p, 'a & b 100%');
    s = await state(p); assert.equal(s.box, 'a & b 100%', 'spaces, & and % survive an address');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
