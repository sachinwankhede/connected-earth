// #520: every continent must be framed with room to spare. A continent whose view needs a zoom at or below the map's minimum cannot be framed, and the camera
// ends pinned at the limit (on a phone this was only Asia). The test picks each continent and checks the camera ends above the minimum zoom.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const CONTINENTS = ['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania'];

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: each continent is framed above the minimum zoom (#520)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
    await p.waitForTimeout(1000);
    const res = {};
    for (const c of CONTINENTS) {
      res[c] = await p.evaluate(async (cont) => {
        const m = window.__M.map; window.__M.go('world', '');
        await new Promise((r) => setTimeout(r, 1500));
        window.__M.go('continent', cont);
        await new Promise((r) => setTimeout(r, 2200));
        return { z: m.getZoom(), min: m.getMinZoom() };
      }, c);
    }
    await b.close();
    for (const c of CONTINENTS) assert.ok(res[c].z >= res[c].min + 0.1, c + ' ends at zoom ' + res[c].z.toFixed(2) + ', the limit is ' + res[c].min + ': ' + JSON.stringify(res));
  });
}

// #520: the camera must not zoom out to the limit on the way (the default fly path did that for Asia on a phone and held there for a second).
test('phone: tapping Asia never zooms out below where it started on the way (#520)', async () => {
  const b = await H.launch(); const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' }); const p = t.page;
  await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
  await p.waitForTimeout(1000);
  const lo = await p.evaluate(async () => {
    const m = window.__M.map; window.__M.go('world', ''); await new Promise((r) => setTimeout(r, 1500));
    let low = 99; const start = m.getZoom(); window.__M.go('continent', 'Asia');
    for (let i = 0; i < 20; i++) { await new Promise((r) => setTimeout(r, 100)); low = Math.min(low, m.getZoom()); }
    return { low, start };
  });
  await b.close();
  assert.ok(lo.low >= lo.start - 0.01, 'lowest zoom on the way ' + lo.low.toFixed(2) + ', it started at ' + lo.start.toFixed(2));
});
