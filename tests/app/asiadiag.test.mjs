// #520 diagnostic (temporary): trace the camera after tapping a continent; the failure message holds a compact trace.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const c of ['Asia', 'Africa']) {
  test(`phone diag ${c}`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, H.SIZES.phone || Object.values(H.SIZES)[0], { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
    await p.waitForTimeout(1000);
    const r = await p.evaluate(async (cont) => {
      const m = window.__M.map; window.__M.go('world', ''); await new Promise((x) => setTimeout(x, 1500));
      let starts = 0, ends = 0; m.on('movestart', () => starts++); m.on('moveend', () => ends++);
      window.__M.go('continent', cont); const tr = [];
      for (let i = 0; i < 12; i++) { await new Promise((x) => setTimeout(x, 300)); const ce = m.getCenter(); tr.push(Math.round(ce.lng) + ',' + Math.round(ce.lat) + ',' + m.getZoom().toFixed(2) + (m.isMoving() ? 'm' : '')); }
      return { starts, ends, tr };
    }, c);
    await b.close();
    assert.fail('DIAG ' + c + ' s' + r.starts + ' e' + r.ends + ' ' + r.tr.join(' '));
  });
}
