// Search says what is true and draws once (#414): a query is drawn when the index has answered (not once per key), "Searching…" while the answer is slow and never "nothing
// found" then, a nothing-found line that says what was searched and offers Clear, a note when the index could not be had, and the query stays in the line inside a region.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const answered = (p, q) => p.waitForFunction((x) => window.__M && window.__M.searched === x, q, { timeout: 60000 });
const stats = (p) => p.evaluate(() => document.getElementById('stats').textContent);
const empty = (p) => p.evaluate(() => { const e = document.getElementById('empty'); return { hidden: e.hidden, text: e.textContent }; });
const cards = (p) => p.evaluate(() => [...document.querySelectorAll('#cards li:not([hidden]) h2')].length);

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: using the search box starts the first search request before any letter is typed (#451)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    const urls = []; p.on('request', (r) => urls.push(r.url()));
    await p.click('#q');
    await p.waitForFunction(() => performance.getEntriesByType('resource').some((e) => /api\/search(-pilot)?\/meta\.json/.test(e.name)), null, { timeout: 15000 });
    assert.ok(urls.some((u) => /api\/search(-pilot)?\/meta\.json/.test(u)), 'meta.json is requested on focus: ' + urls.length + ' requests');
    await p.keyboard.type('elk'); await answered(p, 'elk');
    assert.equal(urls.filter((u) => /api\/search(-pilot)?\/meta\.json/.test(u)).length <= 1, true, 'meta.json is fetched once, not again for the search');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a typed word is drawn about once, not once per key`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.evaluate(() => { window.__n = 0; for (const k of ['pushState', 'replaceState']) { const f = history[k]; history[k] = function () { window.__n++; return f.apply(this, arguments); }; } });   // every draw ends in one address update
    await p.click('#q'); await p.keyboard.type('elk');
    await answered(p, 'elk'); await p.waitForTimeout(800);
    const n = await p.evaluate(() => window.__n);
    assert.ok(n >= 1 && n <= 8, 'draws for six keys: ' + n);   // before: at least two per key (12 or more); now the first letter, the rest as one, and what the local places and the photos add
    assert.match(await stats(p), /places? match “elk”/);
    assert.ok(await cards(p) > 0, 'elk has places');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: nothing found says what was searched and Clear brings the list back`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('zzqxv'); await p.keyboard.press('Enter');
    await answered(p, 'zzqxv');
    let e = await empty(p);
    assert.equal(e.hidden, true, 'the note says it once; no second message');
    assert.equal(await p.evaluate(() => document.getElementById('qnote').textContent), 'No places match “zzqxv”');
    assert.equal(await p.evaluate(() => [qnote, stats].map(e => e.getAttribute('role')).join()), 'status,status', 'the counts are live regions (#591)');
    await p.click('#qclr'); await p.waitForTimeout(500);
    assert.equal(await p.evaluate(() => document.getElementById('q').value), '', 'Clear empties the box');
    e = await empty(p); assert.equal(e.hidden, true, 'the list is back');
    assert.ok(await cards(p) > 0);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: while the index is slow it says "Searching…" and never "nothing found"`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.route(/api\/search(-pilot)?\/(meta|w-|rows-)/, async (route) => { await new Promise((r) => setTimeout(r, 1500)); await route.continue(); });
    await p.click('#q'); await p.keyboard.type('zzqxv');
    await p.waitForTimeout(800);
    assert.equal(await stats(p), 'Searching…', 'a slow answer is announced');
    assert.equal((await empty(p)).hidden, true, 'no "nothing found" while the answer is on its way');
    await answered(p, 'zzqxv');
    assert.equal((await empty(p)).hidden, true, 'the note says it once');
    assert.equal(await p.evaluate(() => document.getElementById('qnote').textContent), 'No places match “zzqxv”');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: when the index cannot be had the card text still filters and a note says so`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.route(/api\/search(-pilot)?\/meta\.json/, (route) => route.abort());
    await p.click('#q'); await p.keyboard.type('yellow'); await p.keyboard.press('Enter');
    await answered(p, 'yellow');
    const s = await stats(p);
    assert.match(s, /places? match “yellow”/); assert.match(s, /Search is limited right now/);
    assert.ok(await cards(p) > 0, 'the card text still finds the place');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: inside a region the line keeps the query`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&s=yellow&r=continent:North%20America' }); const p = t.page;
    await answered(p, 'yellow');
    assert.match(await stats(p), /“yellow” in North America/);
    assert.deepEqual(t.errors, []); await b.close();
  });
}
