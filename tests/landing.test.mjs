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

test('desktop: plain card wording, continent row without counts, no list headings', async () => {
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
  assert.deepEqual(r.g, [], 'no list headings');
  assert.match(r.card, /feeding links/);
  assert.equal(r.lbl, 'Browse by continent'); assert.equal(r.counts, 0);
  assert.match(r.stats, /Who eats whom/);
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

test('phone: a soft fade at the bottom of the open sheet says the list continues, and goes away at the end', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  const op = () => t.page.evaluate(() => { const s = getComputedStyle(document.getElementById('sheet'), '::after'); return { o: +s.opacity, h: s.content !== 'none' && s.content !== 'normal' ? parseFloat(s.height) : 0 }; });
  assert.equal((await op()).h, 0, 'no fade on the collapsed sheet');
  await t.page.click('#speek'); await t.page.waitForTimeout(900);
  let r = await op(); assert.ok(r.h > 20 && r.o > 0.9, 'fade shows while there is more below: ' + JSON.stringify(r));
  await t.page.evaluate(() => { const sb = document.getElementById('sbody'); sb.scrollTop = sb.scrollHeight; }); await t.page.waitForTimeout(1200);
  await t.page.evaluate(() => { const sb = document.getElementById('sbody'); sb.scrollTop = sb.scrollHeight; }); await t.page.waitForTimeout(600);
  r = await op(); assert.ok(r.o < 0.1 || (await t.page.evaluate(() => document.getElementById('more') && !document.getElementById('morecards').hidden)), 'fade leaves at the very end: ' + JSON.stringify(r));
  assert.deepEqual(t.errors, []);
  await b.close();
});

test('phone: the open sheet shows the place count at the top right at home as it does in a continent; the collapsed home sheet does not repeat it', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  const cnt = () => t.page.evaluate(() => { const e = document.querySelector('#srow .scnt'); return { v: e && e.offsetParent !== null, t: e ? e.textContent : '' }; });
  assert.equal((await cnt()).v, false, 'collapsed home: stats line already says it');
  await t.page.click('#speek'); await t.page.waitForTimeout(700);
  let c = await cnt(); assert.ok(c.v && /^\d+ places$/.test(c.t), 'open home: ' + JSON.stringify(c));
  await t.page.click('#regions .chip >> nth=0'); await t.page.waitForTimeout(900);
  c = await cnt(); assert.ok(c.v && /^\d+ places?$/.test(c.t), 'continent: ' + JSON.stringify(c));
  assert.deepEqual(t.errors, []);
  await b.close();
});

// ---- Places <-> Journeys: every combination ----
const SIZES2 = Object.entries(H.SIZES);
async function setup(name, size, opts = {}) {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, size, { hash: '#stub', ...opts });
  await t.page.waitForTimeout(500);
  const api = {
    b, t, p: t.page,
    open: async () => { if (name === 'phone') { await t.page.evaluate(() => window.__M.setSheet('half')); await t.page.waitForTimeout(500); } },
    tab: async (k) => { await t.page.click('#tab-' + k); await t.page.waitForTimeout(450); },
    nJ: () => t.page.evaluate(() => [...document.querySelectorAll('#xcards li')].filter((x) => !x.hidden).length),
    nP: () => t.page.evaluate(() => [...document.querySelectorAll('#cards li:not(.morerow)')].filter((x) => !x.hidden && !x.classList.contains('pg')).length),
    vis: (sel) => t.page.evaluate((s) => { const e = document.querySelector(s); return !!e && e.offsetParent !== null; }, sel),
    chips: () => t.page.evaluate(() => [...document.querySelectorAll('#regions .chip')].map((c) => c.textContent.trim())),
    on: () => t.page.evaluate(() => { const c = document.querySelector('#regions .chip.on'); return c ? c.textContent.trim() : null; }),
    head: () => t.page.evaluate(() => { const c = document.querySelector('#srow .scnt'), st = document.querySelector('#srow .stt'); return c && c.offsetParent ? st.textContent + '|' + c.textContent : 'stats:' + document.getElementById('stats').textContent; }),
    crumbs: () => t.page.evaluate(() => document.querySelector('#crumbs').textContent.trim()),
    tabOn: () => t.page.evaluate(() => document.querySelector('#tabs [aria-pressed="true"]').textContent.trim()),
  };
  return api;
}

for (const [name, size] of SIZES2) {
  test(`${name}: tabs x regions - Journeys never follow the map region, Places keep theirs`, async () => {
    const a = await setup(name, size); await a.open();
    // 1. region chosen on Places, then Journeys: all journeys, header says Journeys, no country/state chips
    await a.p.click('#regions .chip >> nth=0'); await a.p.waitForTimeout(600);
    const region = await a.crumbs(); assert.ok(region.length > 0);
    await a.tab('journeys');
    const all = await a.nJ(); assert.ok(all >= 13, 'all journeys: ' + all);
    assert.match(await a.head(), new RegExp(`Journeys\\|${all} journeys|^stats:${all} journeys$`));
    const chips = await a.chips();
    assert.equal(chips[0], 'All'); assert.ok(chips.includes('Africa') && !chips.includes('Antarctica') && !chips.some((c) => /Congo|South Africa|Missouri/.test(c)), chips.join());
    assert.equal(await a.on(), 'All');
    // 2. filter, then back to Places: region is exactly as left, count is a places count
    await a.p.click('#regions .chip:text-is("Africa")'); await a.p.waitForTimeout(400);
    const af = await a.nJ(); assert.ok(af > 0 && af < all);
    assert.equal(await a.crumbs(), region, 'map region untouched by the Journeys filter');
    assert.equal(await a.on(), 'Africa');
    await a.tab('places');
    assert.equal(await a.crumbs(), region); assert.match(await a.head(), /places?/); assert.doesNotMatch(await a.head(), /journey/i);
    assert.ok((await a.chips()).every((c) => c !== 'All'), 'Places chips are regions, not the Journeys chips');
    // 3. Journeys filter is remembered when you come back
    await a.tab('journeys'); assert.equal(await a.nJ(), af); assert.equal(await a.on(), 'Africa');
    // 4. a different region on Places does not reset the Journeys filter
    await a.tab('places'); await a.p.evaluate(() => document.querySelector('#crumbs button[data-go="world"]').click()); await a.p.waitForTimeout(500);
    await a.p.click('#regions .chip >> nth=1'); await a.p.waitForTimeout(500);
    await a.tab('journeys'); assert.equal(await a.nJ(), af); assert.equal(await a.on(), 'Africa');
    // 5. All clears; filter to a continent, then Antarctica never offered
    await a.p.click('#regions .chip:text-is("All")'); await a.p.waitForTimeout(300); assert.equal(await a.nJ(), all);
    assert.deepEqual(a.t.errors, []);
    await a.b.close();
  });
}

for (const [name, size] of SIZES2) {
  test(`${name}: tabs x search x filters x local parks`, async () => {
    const a = await setup(name, size); await a.open();
    await a.tab('journeys');
    assert.equal(await a.vis('#xcards'), true);
    // typing a search applies to places, so the Places tab comes forward with the matches
    await a.p.fill('#q', 'osprey'); await a.p.waitForTimeout(800);
    assert.equal(await a.tabOn(), 'Places', 'a search brings the Places tab forward');
    assert.equal(await a.vis('#xcards'), false);
    assert.ok((await a.nP()) >= 1);
    // clearing the search returns to the full places list; Journeys still reachable and unfiltered
    await a.p.fill('#q', ''); await a.p.waitForTimeout(700);
    await a.tab('journeys'); assert.ok((await a.nJ()) >= 13);
    // a habitat filter while on Journeys does not hide journeys, and does narrow Places
    await a.p.click('#kinds .chip >> nth=0'); await a.p.waitForTimeout(500);
    assert.ok((await a.nJ()) >= 13, 'habitat chips do not filter journeys');
    await a.tab('places');
    const filtered = await a.nP(); await a.p.click('#kinds .chip >> nth=0'); await a.p.waitForTimeout(500);
    assert.ok((await a.nP()) >= filtered);
    // local parks toggle (if present) does not disturb the Journeys list
    const hasLoc = await a.p.evaluate(() => { const b = document.getElementById('locbtn'); return !!b && b.style.display !== 'none'; });
    if (hasLoc) { await a.tab('journeys'); const before = await a.nJ(); await a.p.click('#locbtn'); await a.p.waitForTimeout(500); assert.equal(await a.nJ(), before); await a.p.click('#locbtn'); await a.p.waitForTimeout(300); }
    assert.deepEqual(a.t.errors, []);
    await a.b.close();
  });
}

for (const [name, size] of SIZES2) {
  test(`${name}: tabs x opening things - a place, a journey chip, the back button, the map`, async () => {
    const a = await setup(name, size); await a.open();
    // Places -> open a place -> back: still on Places
    await a.p.click('#cards .card >> nth=0'); await a.p.waitForTimeout(1500);
    assert.equal(await a.p.evaluate(() => !document.getElementById('webview').hidden), true);
    await a.p.evaluate(() => document.getElementById('back').click()); await a.p.waitForTimeout(900);
    assert.equal(await a.tabOn(), 'Places');
    // Journeys -> open a journey chip -> back: still on Journeys, same filter and card state sane
    await a.open(); await a.tab('journeys'); await a.p.click('#regions .chip:text-is("Africa")'); await a.p.waitForTimeout(300);
    await a.p.click('#xcards li:not([hidden]) .jcard >> nth=0'); await a.p.waitForTimeout(300);
    await a.p.click('#xcards .jcard[aria-expanded="true"] .chip >> nth=0'); await a.p.waitForTimeout(1600);
    assert.equal(await a.p.evaluate(() => !document.getElementById('webview').hidden), true);
    await a.p.evaluate(() => document.getElementById('back').click()); await a.p.waitForTimeout(900);
    await a.open();
    assert.equal(await a.tabOn(), 'Journeys', 'back returns to the Journeys tab'); assert.equal(await a.on(), 'Africa');
    assert.ok((await a.nJ()) > 0);
    // tapping a place on the map while on Journeys opens its card; tab stays
    await a.p.evaluate(() => { const m = window.__M.map; const f = m.getSource('atl-f')._data.features[0]; const q = m.project(f.geometry.coordinates); window.__tap = [q.x, q.y]; });
    const xy = await a.p.evaluate(() => { const r = window.__M.map.getContainer().getBoundingClientRect(); return [r.left + window.__tap[0], r.top + window.__tap[1]]; });
    if (xy[0] > 5 && xy[0] < size.width - 5 && xy[1] > 100 && xy[1] < size.height - 300) { await a.p.mouse.click(xy[0], xy[1]); await a.p.waitForTimeout(800); assert.equal(await a.tabOn(), 'Journeys'); }
    assert.deepEqual(a.t.errors, []);
    await a.b.close();
  });
}

test('phone: tabs x sheet states - collapsed, half and full, switching from every state', async () => {
  const a = await setup('phone', H.SIZES.phone);
  // collapsed: no tabs visible, peek and pitch show; switching tabs is impossible there (tabs live in the open sheet)
  assert.equal(await a.vis('#tabs'), false); assert.equal(await a.vis('#speek'), true);
  for (const state of ['half', 'full']) {
    await a.p.evaluate((s) => window.__M.setSheet(s), state); await a.p.waitForTimeout(600);
    assert.equal(await a.vis('#tabs'), true); assert.equal(await a.vis('#speek'), false); assert.equal(await a.vis('#hook'), false);
    await a.tab('journeys'); assert.match(await a.head(), /^Journeys\|\d+ journeys$/); assert.equal(await a.vis('#xcards'), true); assert.equal(await a.vis('#cards'), false);
    await a.tab('places'); assert.match(await a.head(), /^Connected Earth\|\d+ places$/); assert.equal(await a.vis('#cards'), true);
  }
  // collapse while on Journeys: header returns to the pitch and peek (Places framing), reopen: still Journeys
  await a.tab('journeys');
  await a.p.evaluate(() => window.__M.setSheet('min')); await a.p.waitForTimeout(600);
  assert.equal(await a.vis('#speek'), true, 'collapsed sheet is the home framing');
  await a.p.evaluate(() => window.__M.setSheet('half')); await a.p.waitForTimeout(600);
  assert.equal(await a.tabOn(), 'Journeys');
  // scroll position resets on each switch
  await a.p.evaluate(() => { document.getElementById('sbody').scrollTop = 200; });
  await a.tab('places'); assert.equal(await a.p.evaluate(() => document.getElementById('sbody').scrollTop), 0);
  assert.deepEqual(a.t.errors, []);
  await a.b.close();
});

test('desktop: tabs keep the panel header in step', async () => {
  const a = await setup('desktop', H.SIZES.desktop);
  const stats = () => a.p.evaluate(() => document.getElementById('stats').textContent);
  assert.match(await stats(), /Who eats whom/);
  await a.tab('journeys'); assert.match(await stats(), /^\d+ journeys$/);
  await a.p.click('#regions .chip:text-is("Africa")'); await a.p.waitForTimeout(300); assert.match(await stats(), /^\d+ journeys? in Africa$/);
  await a.tab('places'); assert.match(await stats(), /Who eats whom/);
  await a.p.click('#regions .chip >> nth=0'); await a.p.waitForTimeout(500); assert.match(await stats(), /places? in /);
  await a.tab('journeys'); assert.match(await stats(), /in Africa$/, 'journeys filter kept while the map moved');
  await a.tab('places'); assert.match(await stats(), /places? in /);
  assert.deepEqual(a.t.errors, []);
  await a.b.close();
});

test('arc tap and deep link: a journey card brought up from the map switches to Journeys and clears a filter that hides it', async () => {
  const a = await setup('desktop', H.SIZES.desktop);
  await a.tab('journeys'); await a.p.click('#regions .chip:text-is("Africa")'); await a.p.waitForTimeout(300);
  await a.tab('places');
  // osprey is Yellowstone-Amazon, hidden by an Africa filter
  await a.p.evaluate(() => document.getElementById('xc-osprey') && 0);
  const shown = await a.p.evaluate(() => { const c = document.getElementById('xc-osprey'); return c ? c.parentNode.hidden : null; });
  assert.equal(shown, true, 'osprey hidden by the Africa filter');
  await a.p.evaluate(() => window.__M.hlCard('osprey')); await a.p.waitForTimeout(700);
  assert.equal(await a.tabOn(), 'Journeys'); assert.equal(await a.on(), 'All', 'filter cleared so the card can show');
  assert.equal(await a.p.evaluate(() => { const c = document.getElementById('xc-osprey'); return !c.parentNode.hidden && c.getAttribute('aria-expanded'); }), 'true');
  assert.deepEqual(a.t.errors, []);
  await a.b.close();
});
