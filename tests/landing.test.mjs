import test from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

test('phone: the collapsed sheet pitches the app and peeks at the first place; tapping it opens the sheet', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(600);
  const r = await t.page.evaluate(() => ({ pitch: document.querySelector('#hook .pitch').textContent, stat: document.querySelector('#hook .stat').textContent, peek: document.getElementById('speek').textContent, sheet: document.getElementById('sheet').className }));
  assert.match(r.pitch, /Who eats whom/); assert.doesNotMatch(r.stat, /links/); assert.match(r.peek, /Start here/); assert.match(r.sheet, /s-min/);
  await t.page.click('#speek'); await t.page.waitForTimeout(700);
  assert.match(await t.page.evaluate(() => document.getElementById('sheet').className), /s-half/);
  assert.deepEqual(t.errors, []);
  await b.close();
});

test('desktop: Start here / More places headings, plain card wording, continent row without counts, headings leave with a filter', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.desktop, { hash: '#stub' });
  await t.page.waitForTimeout(600);
  const r = await t.page.evaluate(() => ({
    g: [...document.querySelectorAll('#cards li.grp')].filter((x) => !x.hidden).map((x) => x.textContent),
    card: [...document.querySelectorAll('#cards li:not(.grp) .card')[0].querySelectorAll('.where')].pop().textContent,
    lbl: document.querySelector('#regions .lbl').textContent,
    counts: document.querySelectorAll('#regions .chip b').length,
    stats: document.getElementById('stats').textContent,
    tree: document.getElementById('locbtn').style.display,
  }));
  assert.deepEqual(r.g, ['Start here', 'More places']);
  assert.match(r.card, /feeding links/);
  assert.equal(r.lbl, 'Browse by continent'); assert.equal(r.counts, 0);
  assert.match(r.stats, /Who eats whom/);
  await t.page.click('#kinds .chip >> nth=0'); await t.page.waitForTimeout(500);
  assert.equal(await t.page.evaluate(() => [...document.querySelectorAll('#cards li.grp')].filter((x) => !x.hidden).length), 0, 'no headings while filtering');
  assert.deepEqual(t.errors, []);
  await b.close();
});

test('phone: first batch is about ten places; small regions show everything; no Overview tag; no row label', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(600);
  const r = await t.page.evaluate(() => ({ shown: [...document.querySelectorAll('#cards li:not(.grp):not(.morerow)')].filter((x) => !x.hidden && !x.classList.contains('pg')).length, tag: document.querySelectorAll('#cards .tag').length, lbl: getComputedStyle(document.querySelector('#regions .lbl') || document.body).display }));
  assert.equal(r.shown, 10); assert.equal(r.tag, 0); assert.equal(r.lbl, 'none');
  await t.page.evaluate(() => document.getElementById('sheet') && window.__M.setSheet('half'));
  await t.page.click('#regions .chip >> nth=-1'); await t.page.waitForTimeout(900);
  const n = await t.page.evaluate(() => { const vis = [...document.querySelectorAll('#cards li:not(.grp):not(.morerow)')].filter((x) => !x.hidden); return [vis.length, vis.filter((x) => !x.classList.contains('pg')).length]; });
  assert.ok(n[0] > 12 ? n[1] === 10 : n[1] === n[0], 'region batch: ' + n);
  assert.deepEqual(t.errors, []);
  await b.close();
});
