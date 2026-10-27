import test from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

// First view: a few named flagship places with no counts; they fold back into the normal dots once zoomed in.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: world view shows flagships apart from the clusters, and hands them back when zoomed in`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' });
    const n = (id) => t.page.evaluate((i) => window.__M.map.getSource(i)._data.features.length, id);
    const total = await H.dots(t.page);
    assert.equal(await n('atl-f'), 12, 'twelve flagships at the first view');
    assert.equal(await n('atl-fl'), 12);
    assert.equal(await n('atl-e') + 12, total);
    // phone opens over the Atlantic so both Americas and Europe/Africa are in view
    if (name === 'phone') {
      const c = await H.camera(t.page);
      assert.ok(c.lng > -60 && c.lng < 0, 'phone view centred on the Atlantic: ' + JSON.stringify(c));
    }
    // flagship dots are drawn, in the base layer sense
    const drawn = await t.page.evaluate(() => window.__M.map.queryRenderedFeatures({ layers: ['atl-f-pt'] }).length);
    assert.ok(drawn >= 6, 'flagship dots drawn: ' + drawn);
    // zoomed in, they join the ordinary dots again
    await H.jump(t.page, [-100, 40], 4.5);
    await t.page.waitForTimeout(800);
    assert.equal(await n('atl-f'), 0);
    assert.ok(await H.dots(t.page) >= total, 'no place lost when flagships rejoin the dots');
    // zoom out again and they come back
    await H.jump(t.page, [-20, 25], 1);
    await t.page.waitForTimeout(800);
    assert.equal(await n('atl-f'), 12);
    assert.equal(await H.dots(t.page), total);
    // tapping a flagship opens its place
    const p = await t.page.evaluate(() => { const m = window.__M.map, f = m.getSource('atl-f')._data.features.find((x) => x.properties.id === 'amazon'); m.jumpTo({ center: f.geometry.coordinates, zoom: 2 }); return null; });
    await t.page.waitForTimeout(800);
    const xy = await t.page.evaluate(() => { const m = window.__M.map, f = m.getSource('atl-f')._data.features.find((x) => x.properties.id === 'amazon'); const q = m.project(f.geometry.coordinates), r = m.getContainer().getBoundingClientRect(); return [r.left + q.x, r.top + q.y]; });
    await t.page.mouse.click(xy[0], xy[1]);
    await t.page.waitForTimeout(800);
    const shown = await t.page.evaluate(() => (document.getElementById('peek') && !document.getElementById('peek').hidden && document.getElementById('peek').textContent) || '');
    assert.match(shown, /Amazon/);
    assert.deepEqual(t.errors, []);
    await b.close();
  });
}

// Small dots at first: not tappable until they have grown; tapping near them zooms in instead.
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: first-view dots are tiny and untappable, grow with zoom, and a tap beside them zooms in`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' });
    const rad = () => t.page.evaluate(() => JSON.stringify(window.__M.map.getPaintProperty('atl-n-pt', 'circle-radius')));
    assert.match(await rad(), /1\.4/, 'needle-sized at the first view');
    assert.equal(await t.page.evaluate(() => window.__M.map.getLayoutProperty('atl-cl', 'visibility')), 'none', 'no clusters at the first view');
    // pick a small, ordinary dot that is clear of flagships and clusters
    const xy = await t.page.evaluate(() => {
      const m = window.__M.map, r = m.getContainer().getBoundingClientRect(), W = r.width, Hh = r.height;
      const f = m.queryRenderedFeatures({ layers: ['atl-n-pt'] }).filter((x) => { const p = m.project(x.geometry.coordinates); return p.x > 40 && p.x < W - 60 && p.y > 160 && p.y < Hh - 120 && (W > 700 ? p.x > 430 : true); })[0];
      if (!f) return null; const p = m.project(f.geometry.coordinates); return { x: r.left + p.x, y: r.top + p.y, z: m.getZoom() };
    });
    assert.ok(xy, 'found a small dot');
    await t.page.mouse.click(xy.x, xy.y);
    await t.page.waitForTimeout(900);
    const open = await t.page.evaluate(() => { const p = document.getElementById('peek'); return !!(p && !p.hidden); });
    const z = await t.page.evaluate(() => window.__M.map.getZoom());
    assert.equal(open, false, 'small dot does not open a place');
    assert.ok(z > xy.z + 0.5, 'tap beside the dots zooms in: ' + xy.z + ' -> ' + z);
    // zoomed in: normal size
    await H.jump(t.page, [-90, 38], 5);
    await t.page.waitForTimeout(800);
    assert.equal(await t.page.evaluate(() => window.__M.map.getLayoutProperty('atl-n-pt', 'visibility')), 'none');
    assert.equal(await t.page.evaluate(() => window.__M.map.getLayoutProperty('atl-cl', 'visibility')), 'visible', 'clusters come back once zoomed in');
    assert.deepEqual(t.errors, []);
    await b.close();
  });
}

// Names read white on a dark halo over satellite imagery, dark on a light halo on the plain/street maps.
test('place names flip to white on the satellite view and stay dark on plain maps', async () => {
  const b = await H.launch();
  const col = (t) => t.page.evaluate(() => window.__M.map.getPaintProperty('atl-f-lb', 'text-color'));
  const plain = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  assert.notEqual(await col(plain), '#ffffff');
  const sat = await H.open(b, H.MAIN, H.SIZES.phone, {});
  const c = await sat.page.evaluate(() => { const m = window.__M.map; return m.getStyle().name === 'satellite' ? m.getPaintProperty('atl-f-lb', 'text-color') : 'left-satellite'; });
  assert.ok(c === '#ffffff' || c === 'left-satellite', 'satellite labels are white: ' + c);
  await b.close();
});

// Brighter dot colours on satellite only, and the filter chips always match the map dots.
test('satellite uses the brighter colours and the chips match; plain maps keep the originals', async () => {
  const b = await H.launch();
  const chip = (t) => t.page.evaluate(() => getComputedStyle(document.querySelector('#kinds .chip i.kd')).backgroundColor);
  const dot = (t) => t.page.evaluate(() => { const f = window.__M.map.getSource('atl-f')._data.features[0]; return f.properties.kc; });
  const plain = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' });
  assert.equal(await chip(plain), 'rgb(47, 125, 79)', 'plain: original forest green');
  const sat = await H.open(b, H.MAIN, H.SIZES.phone, {});
  const on = await sat.page.evaluate(() => window.__M.map.getStyle().name === 'satellite');
  if (on) {
    assert.equal(await chip(sat), 'rgb(67, 199, 121)', 'satellite: brighter forest green');
    assert.match(await dot(sat), /#(43c779|8a6fc0|b79cff|2f7d4f)/i);
    const f = await sat.page.evaluate(() => { const fs = window.__M.map.getSource('atl-f')._data.features; return fs.every((x) => /^#[0-9a-f]{6}$/i.test(x.properties.kc)); });
    assert.ok(f);
  }
  await b.close();
});
