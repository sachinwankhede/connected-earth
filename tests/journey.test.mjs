import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  async function start(hash = '#stub') {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash });
    const errors = []; t.page.on('pageerror', (e) => errors.push(String(e)));
    await t.page.waitForTimeout(700);
    return { b, p: t.page, errors };
  }
  const shown = (p) => p.evaluate(() => ({ page: !document.getElementById('jview').hidden, map: !document.getElementById('mapview').hidden, web: !document.getElementById('webview').hidden, hash: location.hash, title: (document.querySelector('#jview h2') || {}).textContent }));

  test(`${name}: a journey page has the route, the story, both ends, sources and more journeys`, async () => {
    const { b, p, errors } = await start();
    await p.evaluate(() => window.__M.showJourney('knot')); await p.waitForTimeout(500);
    const s = await shown(p);
    assert.equal(s.page, true); assert.equal(s.map, false); assert.equal(s.title, 'Red knot'); assert.match(s.hash, /j=knot/);
    const r = await p.evaluate(() => {
      const j = document.getElementById('jview');
      return { heads: [...j.querySelectorAll('h3')].map((h) => h.textContent), land: j.querySelectorAll('.jl').length, arc: !!j.querySelector('.jarc'), dots: j.querySelectorAll('.jpt').length, ends: j.querySelectorAll('.jend').length, src: [...j.querySelectorAll('details.srcd .srcs a')].every((a) => /^https:\/\/en\.wikipedia\.org\/wiki\//.test(a.href)) && j.querySelectorAll('details.srcd .srcs a').length, srcClosed: !j.querySelector('details.srcd').open, endH: Math.round(j.querySelector('.jend').getBoundingClientRect().height), more: j.querySelectorAll('.jmore button').length, when: !!j.querySelector('.jwhen'), over: document.documentElement.scrollWidth - document.documentElement.clientWidth, labels: [...j.querySelectorAll('.jmap text:not(.jemo)')].map((t) => t.textContent) };
    });
    assert.deepEqual(r.heads, ['The story', 'Places on this route', 'More journeys']);
    assert.ok(r.srcClosed, 'sources start collapsed'); assert.ok(r.endH <= 96, 'compact place row: ' + r.endH);
    assert.ok(r.land > 100 && r.arc && r.dots === 2 && r.ends === 2 && r.src >= 1 && r.more >= 1 && r.when);
    assert.deepEqual(r.labels, ['Wadden Sea', "Banc d'Arguin"]);
    assert.ok(r.over <= 1, 'no sideways scroll: ' + r.over);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: every journey opens without errors and with its two places`, async () => {
    const { b, p, errors } = await start();
    const ids = await p.evaluate(() => [...document.querySelectorAll('#xcards .jcard')].map((c) => c.id.slice(3)));
    assert.ok(ids.length >= 13);
    for (const id of ids) {
      await p.evaluate((i) => window.__M.showJourney(i), id);
      const r = await p.evaluate(() => ({ h: document.querySelector('#jview h2').textContent, ends: document.querySelectorAll('#jview .jend').length, pts: window.__M.jpts.length, nan: window.__M.jpts.some((q) => !isFinite(q[0]) || !isFinite(q[1])), inside: window.__M.jpts.every((q) => q[0] > -50 && q[0] < 1000 && q[1] > -50 && q[1] < 700), more: document.querySelectorAll('#jview .jmore button').length }));
      assert.ok(r.h && r.ends === 2 && r.pts === 41 && !r.nan && r.inside && r.more >= 1, id + ' ' + JSON.stringify(r));
    }
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: the play label fits the traveller, the map shows its icon, places describe the species, and type sizes match the rest of the app`, async () => {
    const { b, p, errors } = await start();
    const label = async (id) => { await p.evaluate((i) => window.__M.showJourney(i), id); await p.waitForTimeout(900); return p.evaluate(() => ({ go: document.querySelector('#jview .jplay').textContent.trim(), mark: document.getElementById('jemo').textContent.trim(), aria: document.getElementById('jfly').getAttribute('aria-label') })); };
    assert.equal((await label('knot')).go, 'Fly the route');
    const sock = await label('sockeye'); assert.equal(sock.go, 'Swim the route'); assert.ok(sock.mark.length > 0); assert.equal(sock.aria, 'Swim the route');
    assert.equal((await label('greenturtleA')).go, 'Swim the route');
    assert.equal((await label('caribouwest')).go, 'Follow the herd');
    assert.equal((await label('dust')).go, 'Follow the dust');
    assert.equal((await label('nutrients')).go, 'Follow the water');
    await p.evaluate(() => window.__M.showJourney('knot')); await p.waitForTimeout(1500);
    const r = await p.evaluate(() => { const f = (s) => { const c = getComputedStyle(document.querySelector(s)); return c.fontSize + '/' + c.fontWeight; }; return { roles: [...document.querySelectorAll('#jview .jrole')].map((x) => x.textContent.trim().length), h2: f('#jview h2'), body: f('#jview .jwhen'), h3: f('#jview h3'), kind: f('#jview .jkind'), card: f('#jview .jmore b') }; });
    assert.ok(r.roles.length === 2 && r.roles.every((n) => n > 20), 'each place says what the species does there: ' + r.roles);
    assert.equal(r.h2, '24px/700'); assert.equal(r.body, '14px/400'); assert.equal(r.h3, '11px/500'); assert.equal(r.kind, '11px/500'); assert.equal(r.card, '16px/700');
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: Fly the route moves the dot along the arc and a round trip ends where it began`, async () => {
    const { b, p, errors } = await start();
    await p.evaluate(() => window.__M.showJourney('osprey')); await p.waitForTimeout(300);
    const at = () => p.evaluate(() => { const d = document.getElementById('jdot'); return [+d.getAttribute('cx'), +d.getAttribute('cy')]; });
    const a0 = await at();
    await p.click('#jfly');
    await p.waitForFunction((s) => { const d = document.getElementById('jdot'); return Math.hypot(+d.getAttribute('cx') - s[0], +d.getAttribute('cy') - s[1]) > 20; }, a0, { timeout: 20000 });
    await p.waitForFunction(() => window.__M.jdone >= 1, null, { timeout: 20000 });
    const end = await at(); assert.ok(Math.hypot(end[0] - a0[0], end[1] - a0[1]) < 2, 'species round trip returns to the start');
    // a nutrient flow is one way
    await p.evaluate(() => window.__M.showJourney('dust')); await p.waitForTimeout(300);
    const f0 = await at(); await p.click('#jfly');
    await p.waitForFunction(() => window.__M.jdone >= 2, null, { timeout: 20000 });
    const f1 = await at(); assert.ok(Math.hypot(f1[0] - f0[0], f1[1] - f0[1]) > 50, 'a flow ends at the far place');
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: satellite tiles cover the route map when they load and the plain map shows when they do not`, async () => {
    const { b, p, errors } = await start();
    const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYPj/HwADAgH/9v0BNgAAAABJRU5ErkJggg==', 'base64');
    // blocked (the default in tests): plain map, no satellite look
    for (const id of ['knot', 'dust', 'osprey']) {
      await p.evaluate((i) => window.__M.showJourney(i), id); await p.waitForTimeout(500);
      const r = await p.evaluate(() => ({ sat: !!document.querySelector('.jmap.sat'), land: document.querySelectorAll('.jmap .jl').length, tiles: document.querySelectorAll('.jmap .jt').length }));
      assert.equal(r.sat, false, id + ' plain'); assert.ok(r.land > 100, id + ' land drawn');
    }
    // available: tiles cover the map, labels stay, the credit shows
    await p.route(/arcgisonline/, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: PNG }));
    for (const id of ['knot', 'dust', 'osprey', 'sockeye', 'greenturtleA']) {
      await p.evaluate((i) => window.__M.showJourney(i), id); await p.waitForTimeout(1200);
      const r = await p.evaluate(() => { const m = document.querySelector('.jmap'); const svg = m.querySelector('svg').getBoundingClientRect(); return { sat: m.classList.contains('sat'), tiles: m.querySelectorAll('.jt').length, shown: [...m.querySelectorAll('.jt')].filter((t) => t.getAttribute('opacity') === '1').length, attr: getComputedStyle(m.querySelector('.jattr')).display, labels: m.querySelectorAll('text:not(.jemo)').length, over: document.documentElement.scrollWidth - document.documentElement.clientWidth }; });
      assert.equal(r.sat, true, id + ' satellite'); assert.ok(r.tiles >= 1 && r.tiles <= 36 && r.shown === r.tiles, id + ' tiles ' + JSON.stringify(r)); assert.equal(r.attr, 'block'); assert.equal(r.labels, 2); assert.ok(r.over <= 0);
    }
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: the play button stays small and clear of the route and its places on every journey, and no stray dots clutter the map`, async () => {
    const { b, p, errors } = await start();
    const ids = await p.evaluate(() => window.__M.journeyIds());
    for (const id of ids) {
      await p.evaluate((i) => window.__M.showJourney(i), id); await p.waitForTimeout(350);
      const r = await p.evaluate(() => {
        const m = document.getElementById('jfly'), s = m.querySelector('svg'), mr = m.getBoundingClientRect(), pr = m.querySelector('.jplay').getBoundingClientRect(), k = mr.width / s.viewBox.baseVal.width;
        const hit = window.__M.jpts.filter((q) => { const x = mr.left + q[0] * k, y = mr.top + q[1] * k; return x > pr.left - 14 && x < pr.right + 14 && y > pr.top - 14 && y < pr.bottom + 14; }).length;
        return { hit, w: Math.round(pr.width), h: Math.round(pr.height), near: m.querySelectorAll('.jnear').length, inside: pr.left >= mr.left && pr.right <= mr.right && pr.bottom <= mr.bottom };
      });
      assert.equal(r.hit, 0, id + ' button covers the route'); assert.equal(r.near, 0); assert.ok(r.inside && r.h <= 40 && r.w <= 170, id + ' ' + JSON.stringify(r));
    }
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: back, more journeys, the food web and the link in a food web all connect`, async () => {
    const { b, p, errors } = await start();
    if (name === 'phone') { await p.click('#speek'); await p.waitForTimeout(500); }
    await p.click('[data-tab="journeys"]:visible'); await p.waitForTimeout(400);
    const first = await p.evaluate(() => document.querySelector('#xcards li:not([hidden]) .jcard').id.slice(3));
    await p.click('#xcards li:not([hidden]) .jcard >> nth=0'); await p.waitForTimeout(400);
    assert.equal((await shown(p)).page, true);
    // each more-journeys row has a picture slot, filled from the journey's own photo
    const mj = await p.evaluate(() => { const bt = document.querySelector('#jview .jmore button'); const id = bt.dataset.jj, slot = bt.querySelector('.jmimg'); const x = document.getElementById('xi-' + id); x.innerHTML = '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="">'; window.__M.showJourney(window.__M.jid); return { slot: !!slot, filled: !!document.querySelector('#jview .jmore .jmimg img') }; });
    assert.ok(mj.slot && mj.filled, 'more journeys rows show a photo');
    // more journeys -> another page
    const t1 = (await shown(p)).title;
    await p.click('#jview .jmore button >> nth=0'); await p.waitForTimeout(400);
    const t2 = (await shown(p)).title; assert.notEqual(t1, t2); assert.equal(await p.evaluate(() => document.getElementById('jview').scrollTop), 0);
    // food web, and back lands on the same journey
    await p.click('#jview [data-jopen] >> nth=0'); await p.waitForTimeout(1500);
    let s = await shown(p); assert.equal(s.web, true); assert.equal(s.page, false);
    assert.match(await p.evaluate(() => document.getElementById('back').textContent), /Journey/);
    await p.evaluate(() => document.getElementById('back').click()); await p.waitForTimeout(500);
    s = await shown(p); assert.equal(s.page, true); assert.equal(s.title, t2);
    // back to the list: Journeys tab, that card highlighted
    await p.click('#jview [data-jback]'); await p.waitForTimeout(600);
    s = await shown(p); assert.equal(s.page, false); assert.equal(s.map, true);
    assert.equal(await p.evaluate(() => window.__M.tab), 'journeys');
    assert.equal(await p.evaluate(() => /-j=|j=/.test(location.hash)), false, 'hash cleared');
    // a place's own food web links to its journey
    await p.evaluate(() => window.__M.showJourney('osprey')); await p.waitForTimeout(300);
    await p.click('#jview [data-jopen] >> nth=0'); await p.waitForTimeout(1500);
    const link = await p.evaluate(() => { const x = document.querySelector('#panel [data-journey], [data-journey]'); return x ? x.getAttribute('data-journey') : null; });
    if (link) { await p.evaluate(() => document.querySelector('[data-journey]').click()); await p.waitForTimeout(400); assert.equal((await shown(p)).page, true); }
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: a shared journey link opens the page, and the browser keeps it on reload`, async () => {
    const { b, p, errors } = await start('#stub&j=pelican');
    await p.waitForTimeout(800);
    const s = await shown(p); assert.equal(s.page, true); assert.equal(s.title, 'American white pelican');
    await p.reload(); await p.waitForTimeout(1200);
    assert.equal((await shown(p)).page, true);
    await p.evaluate(() => { location.hash = '#stub&j=nope'; }); await p.waitForTimeout(300);
    assert.equal((await shown(p)).page, true, 'an unknown journey leaves the current page alone');
    await p.click('[data-jback]'); await p.waitForTimeout(500);
    assert.equal((await shown(p)).map, true);
    assert.deepEqual(errors, []); await b.close();
  });

  test(`${name}: tapping a route drawn on the map opens its journey page`, async () => {
    const { b, p, errors } = await start();
    await p.evaluate(() => window.__M.showTies('yellowstone')); await p.waitForTimeout(900);
    await p.evaluate(() => { const m = window.__M.map, f = m.getSource('atl-arc')._data.features[0]; const c = f.geometry.coordinates, q = c[20]; m.jumpTo({ center: q, zoom: 3 }); });
    await p.waitForTimeout(1200);
    const xy = await p.evaluate(() => { const m = window.__M.map, f = m.getSource('atl-arc')._data.features[0], q = m.project(f.geometry.coordinates[20]), r = m.getContainer().getBoundingClientRect(); return { x: r.left + q.x, y: r.top + q.y, id: f.properties.id }; });
    await p.mouse.click(xy.x, xy.y); await p.waitForTimeout(800);
    const s = await shown(p); assert.equal(s.page, true, 'route tap opened ' + xy.id); assert.match(s.hash, new RegExp('j=' + xy.id));
    assert.deepEqual(errors, []); await b.close();
  });
}
