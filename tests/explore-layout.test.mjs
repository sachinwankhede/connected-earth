import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const places = new Map(H.readPlaces(false).map((place) => [place.id, place]));
function assertEquivalentLayout(actual, expected, message) {
  assert.deepEqual(actual.map(([id, label]) => [id, label]), expected.map(([id, label]) => [id, label]), message);
  actual.forEach(([id, , x, y], i) => {
    assert.ok(Math.abs(x - expected[i][2]) <= 5 && Math.abs(y - expected[i][3]) <= 5, `${message}: ${id} moved more than 5px`);
  });
}

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: Explore reuses only matching settled layouts`, async () => {
    const browser = await H.launch();
    const t = await H.open(browser, H.MAIN, size, { hash: '#stub' });
    const p = t.page;
    await p.route('**/photos/species.json', (route) => route.fulfill({ contentType: 'application/json', body: '{}' }));
    const openWeb = async (id) => {
      await p.evaluate((ecoId) => { location.hash = '#stub&e=' + ecoId; }, id);
      await p.waitForFunction(() => {
        const view = document.getElementById('webview'), loading = document.getElementById('webload');
        return view && !view.hidden && loading && loading.hidden && document.querySelector('#svg .node');
      }, null, { timeout: 60000 });
    };
    const returnToMap = async (id) => {
      await p.evaluate((ecoId) => window.__M.showPlace(ecoId), id);
      await p.waitForSelector('#pview [data-pback]', { timeout: 60000 });
      await p.click('#pview [data-pback]');
      await p.waitForFunction(() => !document.getElementById('mapview').hidden, null, { timeout: 60000 });
    };
    const snapshot = () => p.evaluate(() => ({
      layout: window.__M.layoutInfo,
      nodes: [...document.querySelectorAll('#svg .node')].map((node) => {
        const d = node.__data__;
        return [d.id, node.textContent.trim(), d.x, d.y];
      }),
      edges: document.querySelectorAll('#svg .edge').length,
      heading: document.querySelector('#h1')?.textContent.trim(),
    }));

    try {
      await openWeb('yellowstone');
      const cold = await snapshot();
      assert.equal(cold.layout.cacheHit, false, JSON.stringify(cold.layout));
      assert.equal(cold.layout.ticks, 120);
      assert.equal(cold.heading, 'Greater Yellowstone');
      assert.deepEqual(cold.nodes.map(([id]) => id), places.get('yellowstone').nodes.map((node) => node.id));
      assert.equal(cold.edges, places.get('yellowstone').raw.length);
      assert.ok(cold.nodes.every(([, , x, y]) => Number.isFinite(x) && Number.isFinite(y)));

      await returnToMap('yellowstone');
      await openWeb('yellowstone');
      const warm = await snapshot();
      assert.equal(warm.layout.cacheHit, true, JSON.stringify(warm.layout));
      assert.equal(warm.layout.ticks, 0);
      assertEquivalentLayout(warm.nodes, cold.nodes, 'warm reopen restores the graph layout');
      assert.equal(warm.edges, cold.edges);

      await returnToMap('yellowstone');
      await openWeb('serengeti');
      const other = await snapshot();
      assert.equal(other.layout.cacheHit, false, JSON.stringify(other.layout));
      assert.equal(other.layout.ticks, 120);
      assert.equal(other.heading, 'Serengeti');
      assert.deepEqual(other.nodes.map(([id]) => id), places.get('serengeti').nodes.map((node) => node.id));
      assert.equal(other.edges, places.get('serengeti').raw.length);

      await returnToMap('serengeti');
      await openWeb('yellowstone');
      const returned = await snapshot();
      assert.equal(returned.layout.cacheHit, true, JSON.stringify(returned.layout));
      assert.equal(returned.layout.ticks, 0);
      assert.deepEqual(returned.nodes.map(([id]) => id), cold.nodes.map(([id]) => id));

      const resized = { width: size.width + 40, height: size.height };
      await p.setViewportSize(resized);
      await returnToMap('yellowstone');
      await openWeb('yellowstone');
      await p.waitForTimeout(3200);
      const resizedCold = await snapshot();
      assert.equal(resizedCold.layout.cacheHit, false, JSON.stringify(resizedCold.layout));
      assert.equal(resizedCold.layout.ticks, 120, 'a changed viewport does not reuse stale coordinates');
      assert.ok(resizedCold.nodes.every(([, , x, y]) => Number.isFinite(x) && Number.isFinite(y)));

      await returnToMap('yellowstone');
      await openWeb('yellowstone');
      const resizedWarm = await snapshot();
      assert.equal(resizedWarm.layout.cacheHit, true, JSON.stringify(resizedWarm.layout));
      assert.equal(resizedWarm.layout.ticks, 0);
      assertEquivalentLayout(resizedWarm.nodes, resizedCold.nodes, 'the resized layout is restored on a matching reopen');
      assert.deepEqual(t.errors, []);
    } finally {
      await t.close();
      await browser.close();
    }
  });
}
