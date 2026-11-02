// The related-places dots and labels on the map must go away whenever the map card closes (no stray labels piled on the map).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const ties = (p) => p.evaluate(() => window.__M.map.getSource('atl-t')._data.features.length);
for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: related-place markers clear when the card closes, a search starts, or the globe button is used`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.map.getSource('atl-t'), null, { timeout: 60000 }); await p.waitForTimeout(1500);
    for (const how of ['close', 'search', 'home']) {
      await p.evaluate(() => window.__M.peek('serengeti')); await p.waitForTimeout(800);
      assert.ok(await ties(p) > 1, how + ': related places shown while the card is open');
      if (how === 'close') await p.evaluate(() => document.querySelector('[data-closepeek]').click());
      if (how === 'search') await p.evaluate(() => { const q = document.getElementById('q'); q.value = 'elk'; q.dispatchEvent(new Event('input', { bubbles: true })); });
      if (how === 'home') await p.evaluate(() => document.getElementById('zhome').click());
      await p.waitForTimeout(800);
      assert.equal(await ties(p), 0, how + ': markers cleared');
      await p.evaluate(() => { const q = document.getElementById('q'); q.value = ''; q.dispatchEvent(new Event('input', { bubbles: true })); });
    }
    assert.deepEqual(t.errors, []); await b.close();
  });
}
