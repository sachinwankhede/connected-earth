// (Fixture build: the search word is yellowstone, a place name. The word elk gave an empty Places list on the fixture set; I did not trace why, only that a place-name word works.)
// A search is part of the address (#412): `s=<text>` is written as you type, a reload or a shared link brings it back, a place opened from a search is a step of its own,
// and Back goes place -> search list -> no search. Text with spaces and & survives. The region view and a search can be in one address.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

const same = async (p, b, msg) => { const a = (await names(p)).slice(0, 10), n = await p.evaluate(() => window.__M.hitsN); b = b.slice(0, 10); assert.deepEqual(a, b, msg + ' -- got ' + a.length + ' ' + JSON.stringify(a.slice(0, 3)) + ' (index hits ' + n + ') expected ' + b.length + ' ' + JSON.stringify(b.slice(0, 3))); };
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
  await p.locator('#cards [data-eco]').first().click({ timeout: 4000 }).catch(() => p.evaluate(() => document.querySelector('#cards [data-eco]').click()));   // a real tap when the card can be reached (a phone sheet may cover it)
  await p.waitForFunction(() => !document.getElementById('pview').hidden && document.querySelector('#pview h2'), null, { timeout: 30000 });
  return id;
};
const trace = [];
const hook = () => { window.__h = []; const ps = history.pushState; history.pushState = function (s, t, u) { window.__h.push('P:' + String(u).split('#')[1]); return ps.apply(this, arguments); }; addEventListener('hashchange', (e) => window.__h.push('H:' + e.newURL.split('#')[1])); addEventListener('popstate', () => window.__h.push('pop')); };   // what the browser did, for a failure message
const mark = async (p, what) => { trace.push(what + ': ' + (await p.evaluate(() => decodeURIComponent(location.hash).replace('#stub&', '') + ' L' + history.length + ' S' + (history.state ? history.state.sp : '-') + ' q=' + document.getElementById('q').value))); };
const back = async (p) => { await p.evaluate(() => history.back()); await H.pause(p, 700); await mark(p, 'after back'); };

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: typing writes s= in the address, a reload brings the same list back, Clear removes it`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await search(p, 'yellowstone');
    let s = await state(p);
    assert.match(s.hash, /(^|&)s=yellowstone($|&)/, 'the search is in the address');
    const before = await names(p), n0 = await p.evaluate(() => window.__M.hitsN);
    assert.ok(before.length > 0, 'something matches yellowstone');
    await p.reload(); await answered(p, 'yellowstone');
    s = await state(p);
    assert.equal(s.box, 'yellowstone', 'the box has the text again after a reload'); assert.equal(s.clr, true, 'and its Clear link');
    await same(p, before, 'the same list after a reload (typed: index hits ' + n0 + ')');
    await p.click('#qclr'); await H.pause(p, 400);
    s = await state(p); assert.equal(s.box, ''); assert.doesNotMatch(s.hash, /(^|&)s=/, 'no search left in the address');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a place opened from a search keeps the search; Back returns to the list, and once more clears the search`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); const p = t.page;
    await p.addInitScript(hook); await p.evaluate(hook);
    await search(p, 'yellowstone');
    const before = await names(p), n0 = await p.evaluate(() => window.__M.hitsN);
    await mark(p, 'searched'); const id = await openFirst(p); await mark(p, 'place opened');
    let s = await state(p);
    assert.match(s.hash, new RegExp('(^|&)s=yellowstone&pg=' + id + '$'), 'the address has the search and the place');
    // reload on the place: the place and the search are both there, and the link back goes to the same list
    await p.reload(); await answered(p, 'yellowstone'); await p.waitForFunction(() => !document.getElementById('pview').hidden && document.querySelector('#pview h2'), null, { timeout: 60000 });
    s = await state(p); assert.equal(s.page, true); assert.equal(s.box, 'yellowstone');
    await mark(p, 'after reload'); await p.click('[data-pback]'); await H.pause(p, 700); await mark(p, 'after link');
    s = await state(p); assert.equal(s.map, true, 'the list is back'); assert.equal(s.box, 'yellowstone', 'with the search');
    assert.doesNotMatch(s.hash, /pg=/); assert.match(s.hash, /(^|&)s=yellowstone$/);
    await same(p, before, 'the same list as before the place (typed: index hits ' + n0 + ')');
    // the browser's Back from a place: open one again, then Back
    await openFirst(p);
    await back(p);
    s = await state(p); assert.equal(s.page, false, 'Back closes the place'); assert.equal(s.map, true); assert.equal(s.box, 'yellowstone', 'and keeps the search');
    await same(p, before, 'the same list');
    // Back again: the search is cleared before leaving
    await back(p);
    s = await state(p); assert.equal(s.box, '', 'Back from the search list clears the text -- events ' + (await p.evaluate(() => window.__h.join(' '))) + '\n' + trace.slice().reverse().slice(0, 4).join('\n')); assert.doesNotMatch(s.hash, /(^|&)s=/);
    assert.equal(s.clr, false);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a shared link with a search opens it, also with a region and with special characters`, async () => {
    let b = await H.launch(); let t = await H.open(b, H.FMAIN, size, { hash: '#stub&s=yellowstone' }); let p = t.page;
    await answered(p, 'yellowstone');
    let s = await state(p);
    assert.equal(s.box, 'yellowstone'); assert.equal(s.clr, true); assert.equal(s.map, true);
    assert.ok((await names(p)).length > 0, 'the list is filtered');
    assert.deepEqual(t.errors, []); await b.close();

    b = await H.launch(); t = await H.open(b, H.FMAIN, size, { hash: '#stub&s=yellowstone&r=continent:North%20America' }); p = t.page;
    await answered(p, 'yellowstone');
    s = await state(p);
    assert.equal(s.box, 'yellowstone', 'the search and the region together');
    assert.match(s.hash, /(^|&)s=yellowstone&r=continent:North America$/, 'both stay in the address');
    assert.deepEqual(t.errors, []); await b.close();

    b = await H.launch(); t = await H.open(b, H.FMAIN, size, { hash: '#stub' }); p = t.page;
    await p.click('#q'); await p.keyboard.type('a & b 100%'); await p.keyboard.press('Enter'); await answered(p, 'a & b 100%');
    await p.reload(); await answered(p, 'a & b 100%');
    s = await state(p); assert.equal(s.box, 'a & b 100%', 'spaces, & and % survive an address');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
