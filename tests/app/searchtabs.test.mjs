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

  test(`${name}: Places lists the places whose name or region has the word, not every place with a bear in it (#480)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('bear'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'bear' && /places? match/.test(document.getElementById('qnote').textContent), null, { timeout: 60000 });
    const r = await p.evaluate(() => { const li = [...document.querySelectorAll('#cards li:not([hidden]) .card')]; return { n: li.length, bad: li.filter((c) => !/bear/i.test(c.querySelector('h2').textContent + ' ' + c.querySelector('.where').textContent)).length, note: document.getElementById('qnote').textContent }; });
    assert.ok(r.n > 0, 'some places have bear in the name or region'); assert.equal(r.bad, 0, 'every listed place has bear in its name or region');
    assert.match(r.note, new RegExp('^' + r.n + ' places? match'), 'the count is the list');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a search shows the same row on every tab: picture 52px, title, one muted line, chevron (#483)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.click('#q'); await p.keyboard.type('elk'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'elk' && document.querySelector('#cards li:not([hidden]) .card'), null, { timeout: 60000 });
    const box = (sel) => p.evaluate((q) => { const e = [...document.querySelectorAll(q)].find((x) => x.offsetParent), c = getComputedStyle(e);  return { radius: c.borderTopLeftRadius, border: c.borderTopWidth, pad: c.paddingTop + ' ' + c.paddingLeft }; }, sel);
    const boxes = { places: await box('#cards li:not([hidden]) .card') };
    const pl = await p.evaluate(() => { const c = document.querySelector('#cards li:not([hidden]) .card'), i = c.querySelector('.cimg').getBoundingClientRect(), h = c.querySelector('h2').getBoundingClientRect(), w = c.querySelector('.where').getBoundingClientRect();
      return { pic: Math.round(i.width) + 'x' + Math.round(i.height), titleAbove: h.top < w.top, blurb: getComputedStyle(c.querySelector('p')).display, chev: getComputedStyle(c, '::after').content, caps: getComputedStyle(c.querySelector('.where')).textTransform }; });
    assert.deepEqual([pl.pic, pl.titleAbove, pl.blurb, pl.caps], ['52x52', true, 'none', 'none'], 'Places row: ' + JSON.stringify(pl)); assert.match(pl.chev, /\u203a|›/, 'a chevron');
    assert.match(await p.evaluate(() => { const w = document.querySelectorAll('#cards li:not([hidden]) .card .where'); return w[1] && getComputedStyle(w[1]).display !== 'none' ? w[1].textContent : ''; }), /\d+ species · \d+ feeding links/, 'the Places row shows species and feeding links (#508)');
    assert.equal(await p.evaluate(() => getComputedStyle(document.getElementById('qnote')).textTransform), 'none', 'the count line is plain text, not capitals (#481)');
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 }); await p.click('[data-tab="species"]:visible');
    await p.waitForFunction(() => document.querySelector('#sptab .sgl .sgr[data-latin]'), null, { timeout: 60000 });
    const sp = await p.evaluate(() => { const r = document.querySelector('#sptab .sgl .sgr[data-latin]'), i = r.querySelector('.sgi').getBoundingClientRect(), b = r.querySelector('b').getBoundingClientRect(), k = r.querySelector('i').getBoundingClientRect(); return { pic: Math.round(i.width) + 'x' + Math.round(i.height), titleAbove: b.top < k.top, caps: getComputedStyle(r.querySelector('i')).textTransform, chev: !!r.querySelector('svg') }; });
    assert.deepEqual(sp, { pic: '52x52', titleAbove: true, caps: 'none', chev: true }, 'Species row: ' + JSON.stringify(sp));
    boxes.species = await box('#sptab .sgl .sgr[data-latin]');
    assert.deepEqual(boxes.species, boxes.places, 'one list format: Species rows look like Places rows (#493)');
    const j = await p.evaluate(() => !![...document.querySelectorAll('[data-tab="journeys"]')].find((x) => x.offsetParent));
    if (j) {
      await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(500);
      const jc = await p.evaluate(() => { const c = [...document.querySelectorAll('#xcards li')].find((l) => !l.hidden); if (!c) return null; const i = c.querySelector('.jimg').getBoundingClientRect(), h = c.querySelector('.jtitle').getBoundingClientRect(), r = c.querySelector('.jroute').getBoundingClientRect(); return { pic: Math.round(i.width) + 'x' + Math.round(i.height), titleAbove: h.top < r.top, caps: getComputedStyle(c.querySelector('.jroute')).textTransform }; });
      if (jc) assert.deepEqual(jc, { pic: '52x52', titleAbove: true, caps: 'none' }, 'Journeys row: ' + JSON.stringify(jc));
      if (jc) assert.deepEqual(await box('#xcards li:not([hidden]) .jcard'), boxes.places, 'one list format: Journeys rows look like Places rows (#493)');
    }
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: the count line sits close to the tabs and apart from the list (#482, #509)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.click('#q'); await p.keyboard.type('elk'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'elk' && /places? match/.test(document.getElementById('qnote').textContent) && document.querySelector('#cards li:not([hidden]) .card'), null, { timeout: 60000 });
    const g = await p.evaluate(() => { const n = document.getElementById('qnote'), r = n.getBoundingClientRect(), vis = (e) => e && e.offsetParent && e.getBoundingClientRect().height > 0; let a = n.previousElementSibling, z = n.nextElementSibling; while (a && !vis(a)) a = a.previousElementSibling; while (z && !vis(z)) z = z.nextElementSibling;
      return { above: Math.round(r.top - (a ? a.getBoundingClientRect().bottom : n.parentElement.getBoundingClientRect().top)), below: Math.round(z.getBoundingClientRect().top - r.bottom), prev: a ? a.id || a.className : 'parent', next: z.id || z.className }; });   // the space to the neighbours that are on the screen
    assert.ok(g.above <= 10 && g.below >= 6 && g.above <= g.below, 'the count line sits close to the tabs and apart from the list (#509): ' + JSON.stringify(g));
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: in a search the Journeys chips count the matching journeys, one message says none, and the title line does not repeat the count (#495, #496)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="journeys"]:visible', { timeout: 60000 });
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'osprey' && /places? match/.test(document.getElementById('qnote').textContent), null, { timeout: 60000 });
    const sr = await p.evaluate(() => ({ cnt: getComputedStyle(document.querySelector('#srow .scnt')).display, stt: getComputedStyle(document.querySelector('#srow .stt')).display }));
    assert.deepEqual(sr, { cnt: 'none', stt: 'none' }, 'no "Connected Earth, N places" line while searching (the note says it)');
    await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(600);
    const j = await p.evaluate(() => { const n = [...document.querySelectorAll('#xcards li')].filter((l) => !l.hidden).length; const chips = [...document.querySelectorAll('#regions [data-jc] b')].map((x) => +x.textContent); return { n, chips, empty: document.getElementById('jempty').hidden, note: document.getElementById('qnote').textContent }; });
    assert.ok(j.chips.every((c) => c >= 1 && c <= j.n), 'every continent chip counts only the matching journeys (' + j.n + '): ' + JSON.stringify(j.chips));
    if (!j.n) assert.equal(j.empty, true, 'one message, not two: ' + j.note);
    const rep = await p.evaluate(() => ['jintro', 'stats', 'qhead', 'empty'].map((i) => { const e = document.getElementById(i); return e && getComputedStyle(e).display !== 'none' && e.offsetHeight > 0 ? i : null; }).filter(Boolean));
    assert.deepEqual(rep, [], 'on Journeys only the note says what was found (#502)');
    assert.deepEqual(t.errors, []); await b.close();
  });

  if (name === 'phone') test(`${name}: the map fits the search results in the part the open sheet does not cover (#498)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { const m = window.__M.map, f = m.fitBounds.bind(m); window.__fits = []; m.fitBounds = (bb, o) => { window.__fits.push(o && o.padding); return f(bb, o); }; if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.click('#q'); await p.keyboard.type('elk'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'elk' && /places? match/.test(document.getElementById('qnote').textContent), null, { timeout: 60000 });
    await p.waitForFunction(() => window.__fits.some((x) => x && x.bottom >= innerHeight * 0.45), null, { timeout: 15000 }).catch(() => {});
    const pads = await p.evaluate(() => ({ fits: window.__fits, h: innerHeight, sheet: document.getElementById('sheet').className }));
    assert.ok(pads.fits.some((x) => x && x.bottom >= pads.h * 0.45), 'the bottom padding leaves room for the half-open sheet: ' + JSON.stringify(pads));
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: with a search on, every tab says how many it found, and clearing removes the counts`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
    assert.deepEqual((await tabs(p)).slice(0, 2), ['Places', 'Species'], 'no counts without a search');
    await p.click('#q'); await p.keyboard.type('elk'); await p.keyboard.press('Enter');
    await p.waitForFunction(() => window.__M.searched === 'elk', null, { timeout: 60000 });
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
    assert.match(await note(), /^\d+ places? match(es)? “elk”$/, 'Places says what it found');
    await p.click('[data-tab="species"]:visible'); await p.waitForTimeout(600);
    assert.match(await note(), /^\d+ species match(es)? “elk”$/, 'Species says it in the same form');
    if (tx[2]) { await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(400); assert.match(await note(), /^(No|\d+) journeys? match(es)? “elk”$/, 'Journeys too'); }
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
