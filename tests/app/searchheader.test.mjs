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
    await tap(p, '#qhead a[data-hmap]'); await p.waitForFunction(() => document.querySelector('#qhead.qchip') && !document.getElementById('qhead').hidden && document.getElementById('qhead').textContent.startsWith('‹'), null, { timeout: 30000 });
    assert.match((await head(p)).text, /^‹ Osprey · in \d+ places · Species page ›✕$/, 'map mode: a titled screen with a close at its right (#503, 9 Nov)');
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
    await headShown(p); await p.waitForFunction(() => document.getElementById('qhead').classList.contains('qchip') && document.getElementById('qhead').textContent.startsWith('‹'), null, { timeout: 30000 });
    assert.match((await head(p)).text, /^‹ Osprey · in \d+ places · Species page ›✕$/);
    await tap(p, '#qhead a[data-hx]');
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });   // Back goes to the species page the map came from (#503)
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: map mode has continent, country and state pills that narrow the places (#528)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForSelector('#pview [data-spmap]', { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#pview [data-spmap]').click());
    await p.waitForFunction(() => document.getElementById('sheet').classList.contains('mm') && document.querySelectorAll('#regions [data-go]').length > 1 && /in \\d+ place/.test(document.getElementById('qhead').textContent), null, { timeout: 30000 }).catch(() => {});
    const st = () => p.evaluate(() => { const r = document.getElementById('regions'), bx = r.getBoundingClientRect(), h = document.getElementById('qhead').getBoundingClientRect(); return { lead: [...r.querySelectorAll('.leadg .chip')].map((c) => c.textContent), pills: [...r.querySelectorAll('[data-go]')].filter((c) => !c.closest('.leadg')).map((c) => c.getAttribute('data-go') + ':' + c.getAttribute('data-a') + ':' + c.textContent), shown: bx.height > 0 && getComputedStyle(r).display !== 'none', head_first: h.bottom <= bx.top + 1, head: document.getElementById('qhead').textContent, cards: document.querySelectorAll('#cards .card').length, mm: document.getElementById('sheet').classList.contains('mm') }; });
    const a = await st();
    assert.ok(a.mm && a.pills.length > 1 && a.shown, 'pills ' + a.pills.length + ' shown=' + a.shown + ' above=' + a.above + ' mm=' + a.mm); assert.ok(a.head_first, 'the title row is the top row, above the pills');
    assert.ok(a.pills.every((x) => /^continent:/.test(x)) && a.pills.every((x) => /\d$/.test(x)), 'continent pills with counts: ' + a.pills.join(' | '));
    const n0 = +/in (\d+) place/.exec(a.head)[1], k = a.pills[0].split(':')[1];
    await p.evaluate((k2) => document.querySelector('#regions [data-go="continent"][data-a="' + k2.replace(/"/g, '\\"') + '"]').click(), k); await p.waitForTimeout(1500);
    const c = await st(); const n1 = +/in (\d+) place/.exec(c.head)[1];
    assert.ok(c.mm && c.shown && c.pills.length >= 1 && c.pills.every((x) => /^country:/.test(x)), 'the next level is countries: ' + JSON.stringify(c));
    assert.ok(n1 <= n0 && n1 === +/(\d+)$/.exec(a.pills[0])[1], 'the title count follows the pill: ' + n0 + ' -> ' + n1 + ' for ' + a.pills[0]);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: map mode has a ✕ that goes home, and the region path is the first pills of the one pill row (9 Nov)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter');
    await answered(p, 'osprey'); await headShown(p);
    await tap(p, '#qhead a[data-hmap]');
    await p.waitForFunction(() => document.querySelector('#qhead.qchip') && /in \d+ place/.test(document.getElementById('qhead').textContent), null, { timeout: 30000 }); await p.waitForTimeout(2000);
    assert.equal(await p.evaluate(() => !!document.querySelector('#qhead [data-hclose]')), true, 'a close sits on the title row');
    await p.locator('#regions [data-go]').first().click({ timeout: 5000 }); await p.waitForTimeout(1500);   // a continent: the trail now has World
    const y = await p.evaluate(() => { const sr = document.getElementById('srow'), lg = [...document.querySelectorAll('#regions .leadg .chip')]; return { lead: lg.map((c) => c.textContent), on: lg.length > 1 && lg[1].classList.contains('on'), kids: document.querySelectorAll('#regions [data-go]:not(.leadg *)').length, trail: !!document.getElementById('qtrail'), srowShows: [...sr.children].some((c) => c.offsetParent) }; });
    assert.ok(y.lead.length === 2 && /^\u2039 World/.test(y.lead[0]) && /^All /.test(y.lead[1]) && y.on && y.kids >= 1 && !y.trail, 'one row: back pill, All pill, then children: ' + JSON.stringify(y)); assert.equal(y.srowShows, false, 'and not at the top');
    const gap = await p.evaluate(() => { const gr = document.querySelector('#shead .grab'), g = gr.offsetParent ? gr.getBoundingClientRect() : { bottom: document.getElementById('sheet').getBoundingClientRect().top }, h = document.getElementById('qhead').getBoundingClientRect(), sr = document.getElementById('srow').getBoundingClientRect(); return { fromHandle: Math.round(h.top - g.bottom), srowH: Math.round(sr.height) }; });
    assert.ok(gap.srowH === 0 && gap.fromHandle <= 24, 'no empty row above the title and no big gaps: ' + JSON.stringify(gap));   // the top spacing, measured (owner, 9 Nov)
    await p.evaluate(() => document.querySelector('#qhead [data-hclose]').click()); await p.waitForTimeout(1200);
    const home = await p.evaluate(() => ({ mm: document.getElementById('sheet').classList.contains('mm'), q: document.getElementById('q').value, tab: window.__M.tab, lead: !!document.querySelector('#regions .leadg') && !!document.querySelector('#sheet.mm') }));
    assert.deepEqual(home, { mm: false, q: '', tab: 'places', lead: false }, 'the close leaves map mode, clears the search and shows the Places tab');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: from the search header, Show on the map shows the pills in view and a tap on one narrows the places (#528)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter');
    await answered(p, 'osprey'); await headShown(p);
    await tap(p, '#qhead a[data-hmap]');
    await p.waitForFunction(() => document.querySelector('#qhead.qchip') && /in \d+ place/.test(document.getElementById('qhead').textContent), null, { timeout: 30000 }); await p.waitForTimeout(2500);
    const st = () => p.evaluate(() => { const r = document.getElementById('regions'), bx = r.getBoundingClientRect(), sh = document.getElementById('sheet').getBoundingClientRect(), h = document.getElementById('qhead').getBoundingClientRect(), c = r.querySelector('[data-go]'), cb = c && c.getBoundingClientRect(); return { n: r.querySelectorAll('[data-go]').length, disp: getComputedStyle(r).display, rt: Math.round(bx.top), rh: Math.round(bx.height), cb: cb ? Math.round(cb.bottom) : -1, ht: Math.round(h.top), st: Math.round(sh.top), ih: innerHeight, state: window.__M && window.__M.sheetState, sc: document.getElementById('sheet').className, head: document.getElementById('qhead').textContent.trim(), cards: document.querySelectorAll('#cards .card').length }; });
    const a = await st(); const msg = 'n=' + a.n + ' disp=' + a.disp + ' regions top=' + a.rt + ' h=' + a.rh + ' chipBottom=' + a.cb + ' head top=' + a.ht + ' sheet top=' + a.st + ' innerH=' + a.ih + ' state=' + a.state + ' [' + a.sc + ']';
    assert.ok(a.n > 1 && a.rh > 0 && a.cb > 0 && a.cb <= a.ih, 'pills not in view: ' + msg); assert.ok(a.ht + 4 <= a.rt, 'title row is above the pills: ' + msg);
    const n0 = +/in (\d+) place/.exec(a.head)[1];
    await p.locator('#regions [data-go]').first().click({ timeout: 5000 }); await p.waitForTimeout(1500);
    const c = await st(); const n1 = +/in (\d+) place/.exec(c.head)[1];
    assert.ok(n1 <= n0 && c.n >= 1, 'a tap on a pill narrows the places: ' + n0 + ' -> ' + n1 + ' pills ' + c.n + ' state=' + c.state);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a species that sits in one continent and one country still gets pills, one level down (#528)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.route(/api\/species-places\/te\.json/, (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ 'Testus avis': ['yellowstone'] }) }));
    await p.route(/api\/species\/testus-avis\.json/, (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ l: 'Testus avis', n: 'Test bird', tl: 3 }) }));
    await p.evaluate(() => { location.hash = '#stub&sp=testus-avis'; });
    await p.waitForSelector('#pview [data-spmap]', { timeout: 60000 });
    await p.evaluate(() => document.querySelector('#pview [data-spmap]').click());
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-go]').length > 0, null, { timeout: 20000 }).catch(() => {}); await p.waitForTimeout(800);
    const a = await p.evaluate(() => ({ pills: [...document.querySelectorAll('#regions [data-go]')].map((c) => c.getAttribute('data-go') + ':' + c.getAttribute('data-a')), lbl: (document.querySelector('#regions .lbl') || {}).textContent }));
    assert.ok(a.pills.length >= 2 && a.pills.every((x) => /^(country|state):/.test(x)), 'pills one level down: ' + a.pills.join(',') + ' label=' + a.lbl);
    await p.evaluate(() => document.querySelector('#regions [data-go]').click()); await p.waitForTimeout(1200);   // the sheet is not opened here: this species has no header
    assert.ok(await p.evaluate(() => document.querySelectorAll('#cards .card').length) >= 1, 'the place is still listed after a tap on a pill');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
