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
