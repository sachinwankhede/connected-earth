import test from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

test('phone: the collapsed sheet pitches the app and peeks at the first place; tapping it opens the sheet', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(600);
  const r = await t.page.evaluate(() => ({ pitch: document.querySelector('#hook .pitch').textContent, stat: document.querySelector('#hook .stat').textContent, peek: document.getElementById('speek').textContent, sheet: document.getElementById('sheet').className }));
  assert.match(r.pitch, /See how nature is connected/); assert.match(r.stat, /What eats what/); assert.match(r.peek, /Start here/); assert.match(r.sheet, /s-min/);
  await t.page.click('#speek'); await t.page.waitForTimeout(700);
  assert.match(await t.page.evaluate(() => document.getElementById('sheet').className), /s-half/);
  assert.equal(await t.page.evaluate(() => getComputedStyle(document.getElementById('speek')).display), 'none', 'peek goes away once the sheet is open (the list shows the same place)');
  assert.equal(await t.page.evaluate(() => getComputedStyle(document.getElementById('hook')).display), 'none', 'pitch and counts give the space back once the sheet is open');
  assert.deepEqual(t.errors, []);
  await b.close();
});

test('desktop: plain card wording, continent chips carry counts, no list headings', async () => {
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
  assert.equal(r.lbl, 'Browse by continent'); assert.ok(r.counts >= 5, 'continent chips show counts');
  assert.match(r.stats, /See how nature is connected/);
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
    await t.page.click('[data-tab="journeys"]:visible'); await t.page.waitForTimeout(500);
    assert.equal(await vis('#cards'), false); assert.equal(await vis('#xcards'), true);
    const n = await t.page.evaluate(() => ({ cards: document.querySelectorAll('#xcards .jcard').length, route: document.querySelector('#xcards .jroute').textContent }));
    assert.ok(n.cards >= 13); assert.match(n.route, /→/);
    assert.equal(await t.page.evaluate(() => [...document.querySelectorAll('[data-tab="journeys"]')].find((b) => b.offsetParent).textContent.trim()), 'Journeys', 'no count on the tab');
    // a journey card opens its own page; from there a button opens that place's food web
    await t.page.click('#xcards .jcard >> nth=0'); await t.page.waitForTimeout(500);
    assert.equal(await t.page.evaluate(() => !document.getElementById('jview').hidden && document.getElementById('mapview').hidden), true, 'journey page open');
    await t.page.click('#jview [data-jopen] >> nth=0'); await t.page.waitForTimeout(1500);
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
  assert.match(await t.page.evaluate(() => document.getElementById('stats').textContent), /See how nature is connected.*where it travels/);
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

test('phone: tabs come first in the open sheet; the title row only appears for a region, with its count; collapsed home keeps its title', async () => {
  const b = await H.launch();
  const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  await t.page.waitForTimeout(500);
  const cnt = () => t.page.evaluate(() => { const e = document.querySelector('#srow .scnt'); return { v: e && e.offsetParent !== null, t: e ? e.textContent : '' }; });
  assert.equal((await cnt()).v, false, 'collapsed home: stats line already says it');
  await t.page.click('#speek'); await t.page.waitForTimeout(700);
  const rowVis = () => t.page.evaluate(() => !!document.getElementById('srow').offsetParent);
  assert.equal(await rowVis(), false, 'open at home: no title row, the tabs lead');
  const first = await t.page.evaluate(() => { const sh = document.getElementById('sheet').getBoundingClientRect(), tb = document.querySelector('#trow .tabs').getBoundingClientRect(); return tb.top - sh.top; });
  assert.ok(first < 48, 'tabs sit at the top of the open sheet: ' + first);
  let c = { v: true, t: '' };
  await t.page.click('#regions .chip >> nth=0'); await t.page.waitForTimeout(900);
  c = await cnt(); assert.ok(c.v && /^\d+ places?$/.test(c.t), 'continent: ' + JSON.stringify(c));
  assert.equal(await rowVis(), true, 'a region shows its title row (back, name, count) under the tabs');
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
    tab: async (k) => { await t.page.click('[data-tab="' + k + '"]:visible'); await t.page.waitForTimeout(450); },
    nJ: () => t.page.evaluate(() => [...document.querySelectorAll('#xcards li')].filter((x) => !x.hidden).length),
    nP: () => t.page.evaluate(() => [...document.querySelectorAll('#cards li:not(.morerow)')].filter((x) => !x.hidden && !x.classList.contains('pg')).length),
    vis: (sel) => t.page.evaluate((s) => { const e = document.querySelector(s); return !!e && e.offsetParent !== null; }, sel),
    chips: () => t.page.evaluate(() => [...document.querySelectorAll('#regions .chip')].map((c) => c.textContent.trim().replace(/\s+\d+$/, ''))),
    on: () => t.page.evaluate(() => { const c = document.querySelector('#regions .chip.on'); return c ? c.textContent.trim().replace(/\s+\d+$/, '') : null; }),
    head: () => t.page.evaluate(() => { const c = document.querySelector('#srow .scnt'), st = document.querySelector('#srow .stt'); return c && c.offsetParent ? st.textContent + '|' + c.textContent : 'stats:' + document.getElementById('stats').textContent; }),
    crumbs: () => t.page.evaluate(() => document.querySelector('#crumbs').textContent.trim()),
    tabOn: () => t.page.evaluate(() => (window.__M.tab === 'journeys' ? 'Journeys' : 'Places')),
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
    assert.match(await a.p.evaluate(() => document.getElementById('jintro').textContent), new RegExp(`^${all} journeys\\.`));
    if (name === 'phone') assert.equal(await a.vis('#srow'), false, 'no region title row on the Journeys tab');
    else assert.equal(await a.p.evaluate(() => document.getElementById('srow').textContent.trim()), 'Connected Earth');
    const chips = await a.chips();
    assert.equal(chips[0], 'All'); assert.ok(chips.includes('Africa') && !chips.includes('Antarctica') && !chips.some((c) => /Congo|South Africa|Missouri/.test(c)), chips.join());
    assert.equal(await a.on(), 'All');
    // 2. filter, then back to Places: region is exactly as left, count is a places count
    await a.p.click('#regions .chip:text-matches("^Africa")'); await a.p.waitForTimeout(400);
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
    assert.equal(await a.p.evaluate(() => !document.getElementById('pview').hidden), true, 'a place opens its page');
    await a.p.click('#pview [data-pback]'); await a.p.waitForTimeout(900);
    assert.equal(await a.tabOn(), 'Places');
    // Journeys -> open a journey chip -> back: still on Journeys, same filter and card state sane
    await a.open(); await a.tab('journeys'); await a.p.click('#regions .chip:text-matches("^Africa")'); await a.p.waitForTimeout(300);
    await a.p.click('#xcards li:not([hidden]) .jcard >> nth=0'); await a.p.waitForTimeout(300);
    await a.p.click('#jview [data-jopen] >> nth=0'); await a.p.waitForTimeout(1600);
    assert.equal(await a.p.evaluate(() => !document.getElementById('webview').hidden), true);
    await a.p.evaluate(() => document.getElementById('back').click()); await a.p.waitForTimeout(900);
    assert.equal(await a.p.evaluate(() => !document.getElementById('jview').hidden), true, 'back from the food web returns to the journey');
    await a.p.click('#jview [data-jback]'); await a.p.waitForTimeout(700);
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
  assert.equal(await a.vis('#trow .tabs'), false); assert.equal(await a.vis('#speek'), true);
  for (const state of ['half', 'full']) {
    await a.p.evaluate((s) => window.__M.setSheet(s), state); await a.p.waitForTimeout(600);
    assert.equal(await a.vis('#trow .tabs'), true); assert.equal(await a.vis('#speek'), false); assert.equal(await a.vis('#hook'), false);
    await a.tab('journeys'); assert.match(await a.p.evaluate(() => document.getElementById('jintro').textContent), /^\d+ journeys\./); assert.equal(await a.vis('#xcards'), true); assert.equal(await a.vis('#cards'), false); assert.equal(await a.vis('#srow'), false);
    await a.tab('places'); assert.equal(await a.vis('#srow'), false, 'home: tabs lead, no title row'); assert.equal(await a.vis('#cards'), true);
  }
  // collapse while on Journeys: header returns to the pitch and peek (Places framing), reopen: still Journeys
  await a.tab('journeys');
  await a.p.evaluate(() => window.__M.setSheet('min')); await a.p.waitForTimeout(600);
  assert.equal(await a.vis('#speek'), true, 'collapsed sheet is the home framing');
  assert.equal(await a.p.evaluate(() => document.querySelector('#srow .stt').textContent), 'Connected Earth');
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
  assert.match(await stats(), /See how nature is connected/);
  await a.tab('journeys'); assert.match(await stats(), /^\d+ journeys$/);
  await a.p.click('#regions .chip:text-matches("^Africa")'); await a.p.waitForTimeout(300); assert.match(await stats(), /^\d+ journeys? in Africa$/);
  await a.tab('places'); assert.match(await stats(), /See how nature is connected/);
  await a.p.click('#regions .chip >> nth=0'); await a.p.waitForTimeout(500); assert.match(await stats(), /places? in /);
  await a.tab('journeys'); assert.match(await stats(), /in Africa$/, 'journeys filter kept while the map moved');
  await a.tab('places'); assert.match(await stats(), /places? in /);
  assert.deepEqual(a.t.errors, []);
  await a.b.close();
});

test('arc tap and deep link: a journey card brought up from the map switches to Journeys and clears a filter that hides it', async () => {
  const a = await setup('desktop', H.SIZES.desktop);
  await a.tab('journeys'); await a.p.click('#regions .chip:text-matches("^Africa")'); await a.p.waitForTimeout(300);
  await a.tab('places');
  // osprey is Yellowstone-Amazon, hidden by an Africa filter
  await a.p.evaluate(() => document.getElementById('xc-osprey') && 0);
  const shown = await a.p.evaluate(() => { const c = document.getElementById('xc-osprey'); return c ? c.parentNode.hidden : null; });
  assert.equal(shown, true, 'osprey hidden by the Africa filter');
  await a.p.evaluate(() => window.__M.hlCard('osprey')); await a.p.waitForTimeout(700);
  assert.equal(await a.tabOn(), 'Journeys'); assert.equal(await a.on(), 'All', 'filter cleared so the card can show');
  assert.equal(await a.p.evaluate(() => { const c = document.getElementById('xc-osprey'); return !c.parentNode.hidden; }), true);
  assert.deepEqual(a.t.errors, []);
  await a.b.close();
});

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: the region row is a tappable trail; one tap jumps up two levels; one-option rows are hidden`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' });
    await t.page.waitForTimeout(600);
    if (name === 'phone') { await t.page.click('#speek'); await t.page.waitForTimeout(600); }
    const trail = () => t.page.evaluate(() => { const r = document.getElementById('srow'); return { btns: [...r.querySelectorAll('.sbk')].map((x) => x.textContent), cur: r.querySelector('.stt').textContent, vis: r.offsetParent !== null }; });
    await t.page.evaluate(() => window.__M.go ? window.__M.go('state', 'Missouri') : null);
    const viaHash = await t.page.evaluate(() => !!window.__M.go);
    if (!viaHash) { await t.page.goto((await H.urlFor(H.MAIN)) + '#stub&r=state:Missouri'); await t.page.waitForTimeout(1200); if (name === 'phone') { await t.page.click('#speek').catch(() => {}); } }
    await t.page.waitForTimeout(800);
    const s1 = await trail();
    assert.deepEqual(s1.btns, ['World', 'North America', 'United States'], 'full trail above the current state');
    assert.equal(s1.cur, 'Missouri');
    assert.equal(await t.page.evaluate(() => document.querySelectorAll('#regions .chip').length), 0, 'a state has no further chips');
    await t.page.click('#srow .sbk >> nth=1'); await t.page.waitForTimeout(800);
    const s2 = await trail();
    assert.deepEqual(s2.btns, ['World'], 'jumped straight to the continent');
    assert.equal(s2.cur, 'North America');
    // every chip row that is shown offers at least two choices
    const n = await t.page.evaluate(() => document.querySelectorAll('#regions .chip').length);
    assert.ok(n === 0 || n >= 2, 'no single-option chip rows: ' + n);
    await t.page.click('#srow .sbk >> nth=0'); await t.page.waitForTimeout(600);
    assert.equal((await trail()).cur, 'Connected Earth');
    await b.close();
  });
}

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: going up a level with the trail closes an open place card and its highlighted links`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' });
    const p = t.page; await p.waitForTimeout(600);
    if (name === 'phone') { await p.click('#speek'); await p.waitForTimeout(600); }
    await p.click('#regions .chip:text-matches("^Africa")'); await p.waitForTimeout(1200);
    await p.evaluate(() => window.__M.peek('serengeti')); await p.waitForTimeout(1200);
    const open = await p.evaluate(() => ({ tie: window.__M.tieId, tied: window.__M.map.getSource('atl-t')._data.features.length }));
    assert.ok(open.tie && open.tied > 0, 'a place is selected: ' + JSON.stringify(open));
    await p.evaluate(() => document.querySelector('#srow .sbk, #srow button').click()); await p.waitForTimeout(1500);
    const after = await p.evaluate(() => ({ tie: window.__M.tieId, tied: window.__M.map.getSource('atl-t')._data.features.length, peek: document.getElementById('peek').hidden, op: window.__M.map.getPaintProperty('atl-f-pt', 'circle-opacity') }));
    assert.equal(after.tie, null); assert.equal(after.tied, 0, 'no highlighted links left'); assert.equal(after.peek, true); assert.equal(after.op, 1, 'dots are not dimmed');
    await b.close();
  });
}
