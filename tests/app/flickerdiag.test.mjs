// Diagnostic for #520 (the map flickers when a continent, country or state is picked): counts what the map is asked to do after one pick.
import { test } from 'node:test';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: map calls after picking a continent (diagnostic, #520)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
    await p.waitForTimeout(1500);
    const counts = await p.evaluate(async () => {
      const m = window.__M.map, c = {}; const bump = (k) => { c[k] = (c[k] || 0) + 1; };
      for (const fn of ['fitBounds', 'setFilter', 'setPaintProperty', 'setLayoutProperty', 'easeTo', 'flyTo', 'jumpTo', 'setStyle', 'resize']) { const o = m[fn].bind(m); m[fn] = (...a) => { bump(fn + (fn === 'setPaintProperty' || fn === 'setFilter' ? ':' + a[0] : '')); return o(...a); }; }
      for (const id of Object.keys(m.style.sourceCaches || {})) { const s = m.getSource(id); if (s && s.setData) { const o = s.setData.bind(s); s.setData = (d) => { bump('setData:' + id); return o(d); }; } }
      let renders = 0; m.on('render', () => renders++);
      const btn = [...document.querySelectorAll('#regions [data-go]')].find((x) => x.offsetParent);
      if (btn) btn.click();
      await new Promise((r) => setTimeout(r, 3000));
      c.renders = renders; c.clicked = btn ? btn.textContent.trim() : null; return c;
    });
    await b.close();
    throw new Error('DIAG ' + name + ' ' + JSON.stringify(counts));
  });
}
