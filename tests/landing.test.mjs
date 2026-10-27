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
  assert.equal(await t.page.evaluate(() => getComputedStyle(document.getElementById('speek')).display), 'none', 'peek goes away once the sheet is open (the list shows the same place)');
  assert.equal(await t.page.evaluate(() => getComputedStyle(document.getElementById('hook')).display), 'none', 'pitch and counts give the space back once the sheet is open');
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

test('continent, country and state chips run from most places to fewest', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.desktop, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  const counts = () => t.page.evaluate(() => [...document.querySelectorAll('#regions .chip')].map((c) => ({ n: c.textContent.trim(), c: +(c.querySelector('b') || { textContent: -1 }).textContent })));
  const places = await t.page.evaluate(() => [...document.querySelectorAll('#cards li:not(.grp):not(.morerow)')].length);
  // choose a continent, then check the country row order via the number of places in each
  await t.page.click('#regions .chip >> nth=0'); await t.page.waitForTimeout(700);
  const row = await counts();
  const nums = row.map((x) => x.c);
  assert.ok(row.length > 1 && nums.every((x, i) => i === 0 || nums[i - 1] >= x), 'countries by place count: ' + JSON.stringify(row));
  assert.ok(places > 0);
  await b.close();
});

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: Places | Journeys tabs switch the list, journeys are compact route cards that open on tap`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' });
    await t.page.waitForTimeout(600);
    if (name === 'phone') { await t.page.click('#speek'); await t.page.waitForTimeout(600); }
    const vis = (sel) => t.page.evaluate((s) => { const e = document.querySelector(s); return !!e && e.offsetParent !== null; }, sel);
    assert.equal(await vis('#cards'), true); assert.equal(await vis('#xcards'), false, 'journeys hidden on the Places tab');
    await t.page.click('#tab-journeys'); await t.page.waitForTimeout(500);
    assert.equal(await vis('#cards'), false); assert.equal(await vis('#xcards'), true);
    const n = await t.page.evaluate(() => ({ cards: document.querySelectorAll('#xcards .jcard').length, route: document.querySelector('#xcards .jroute').textContent }));
    assert.ok(n.cards >= 13); assert.match(n.route, /→/);
    assert.equal(await t.page.evaluate(() => document.getElementById('tab-journeys').textContent.trim()), 'Journeys', 'no count on the tab');
    assert.equal(await t.page.evaluate(() => getComputedStyle(document.querySelector('#xcards .jjumps')).display), 'none', 'collapsed card hides its chips');
    await t.page.click('#xcards .jcard >> nth=0'); await t.page.waitForTimeout(300);
    assert.equal(await t.page.evaluate(() => getComputedStyle(document.querySelector('#xcards .jjumps')).display), 'flex', 'open card shows its chips');
    // a chip opens that place's food web
    await t.page.click('#xcards .jcard[aria-expanded="true"] .chip >> nth=0'); await t.page.waitForTimeout(1500);
    assert.equal(await t.page.evaluate(() => !document.getElementById('webview').hidden), true);
    assert.deepEqual(t.errors, []);
    await b.close();
  });
}

test('phone: more places load when you scroll to the end of the list, and a quiet link works too; nothing loads before you scroll', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  await t.page.evaluate(() => window.__M.setSheet('full')); await t.page.waitForTimeout(800);
  const shown = () => t.page.evaluate(() => [...document.querySelectorAll('#cards li:not(.grp):not(.morerow)')].filter((x) => !x.hidden && !x.classList.contains('pg')).length);
  assert.equal(await shown(), 10);
  await t.page.waitForTimeout(800);
  assert.equal(await shown(), 10, 'nothing loads until the reader scrolls');
  assert.match(await t.page.evaluate(() => document.getElementById('more').textContent), /Show \d+ more places/);
  await t.page.evaluate(() => { const sb = document.getElementById('sbody'); sb.scrollTop = sb.scrollHeight; });
  await t.page.waitForTimeout(1200);
  const n1 = await shown();
  assert.ok(n1 >= 25, 'next batch loaded on scroll: ' + n1);
  // the link still works for anyone who prefers it
  await t.page.evaluate(() => { const sb = document.getElementById('sbody'); sb.scrollTop = 0; });
  await t.page.waitForTimeout(300);
  await t.page.evaluate(() => { const m = document.getElementById('more'); if (m) m.scrollIntoView({ block: 'center' }); });
  await t.page.click('#more'); await t.page.waitForTimeout(800);
  assert.ok(await shown() > n1, 'link loads another batch');
  assert.deepEqual(t.errors, []);
  await b.close();
});

test('desktop keeps the pitch and counts in the panel', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.desktop, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  assert.match(await t.page.evaluate(() => document.getElementById('stats').textContent), /Who eats whom.*places/);
  await b.close();
});
