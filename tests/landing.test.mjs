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
