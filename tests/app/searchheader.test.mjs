// The result header, the "why" line and the filter chip (#425): an exact species or place gets a header line with a link to its page, the header of a species links to its places on the map,
// a species filter from "Show on the map" is a visible chip that clears, and text that is not an exact match gets no header.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const answered = (p, q) => p.waitForFunction((x) => window.__M && window.__M.searched === x, q, { timeout: 60000 });
const head = (p) => p.evaluate(() => { const h = document.getElementById('qhead'); return { hidden: h.hidden, text: h.textContent.trim(), chip: h.classList.contains('qchip') }; });
const whys = (p) => p.evaluate(() => [...document.querySelectorAll('#cards li:not([hidden]) .why')].map((x) => x.textContent));
const tap = (p, sel) => p.locator(sel).first().click({ timeout: 4000 }).catch(() => p.evaluate((x) => document.querySelector(x).click(), sel));   // a real tap when the link can be reached (a phone sheet may cover it)
const headShown = (p) => p.waitForFunction(() => !document.getElementById('qhead').hidden, null, { timeout: 30000 });

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: an exact species gets a header with a link to its page and its places are one tap away`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter');
    await answered(p, 'osprey'); await headShown(p);
    const h = await head(p);
    assert.match(h.text, /^Osprey · found in \d+ places · Species page ›$/); assert.equal(h.chip, false);
    assert.equal(await p.evaluate(() => document.querySelectorAll('#cards .why').length), 0, 'the list is by name: no why lines');
    await tap(p, '#qhead a[data-hmap]'); await p.waitForFunction(() => document.querySelector('#qhead.qchip'), null, { timeout: 30000 });
    assert.match((await head(p)).text, /^‹ Osprey · in \d+ places · Species page ›$/, 'map mode: a titled screen (#503)');
    assert.deepEqual(await p.evaluate(() => ({ box: document.getElementById('q').value, mm: document.getElementById('sheet').classList.contains('mm'), tabs: [...document.querySelectorAll('[data-tab]')].some((x) => x.offsetParent) })), { box: '', mm: true, tabs: false }, 'the box is empty and the tabs are hidden while the map mode is on');
    await p.click('#qhead a[data-hx]'); await p.waitForTimeout(800);
    assert.equal(await p.evaluate(() => document.getElementById('q').value), 'osprey', 'Back returns to the search the map came from');
    assert.equal(await p.evaluate(() => document.getElementById('sheet').classList.contains('mm')), false, 'and the tabs are back');
    await p.click('#qclr'); await p.waitForTimeout(400);
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter'); await answered(p, 'osprey'); await headShown(p);
    await tap(p, '#qhead a[data-hsp]');
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ Search');
    await p.evaluate(() => history.back()); await p.waitForTimeout(800);
    assert.equal(await p.evaluate(() => document.getElementById('q').value), 'osprey'); assert.equal((await head(p)).hidden, false, 'Back returns to the result with its header');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: text that is not an exact match, and a search with no result, get no header`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('ospr'); await p.keyboard.press('Enter'); await answered(p, 'ospr'); await p.waitForTimeout(800);
    assert.equal((await head(p)).hidden, true);
    await p.click('#qclr'); await p.keyboard.type('zzqxv'); await p.keyboard.press('Enter'); await answered(p, 'zzqxv'); await p.waitForTimeout(500);
    assert.equal((await head(p)).hidden, true);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: an exact place gets a header that opens the place`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    const nm = await p.evaluate(() => document.querySelector('#cards li:not([hidden]) h2').textContent.trim());
    await p.click('#q'); await p.keyboard.type(nm); await p.keyboard.press('Enter'); await answered(p, nm.toLowerCase()); await headShown(p);
    const h = await head(p); assert.ok(h.text.startsWith(nm), h.text); assert.match(h.text, /Open the place ›$/);
    await tap(p, '#qhead a[data-hpl]');
    await p.waitForFunction(() => document.querySelector('#pview h2'), null, { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview h2').textContent.trim()), nm);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: Show on the map opens a map mode whose title goes back to the species page (#503)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForSelector('#pview [data-spmap]', { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#pview [data-spmap]').click());
    await headShown(p); await p.waitForFunction(() => document.getElementById('qhead').classList.contains('qchip'), null, { timeout: 30000 });
    assert.match((await head(p)).text, /^‹ Osprey · in \d+ places · Species page ›$/);
    await tap(p, '#qhead a[data-hx]');
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });   // Back goes to the species page the map came from (#503)
    assert.deepEqual(t.errors, []); await b.close();
  });
}
