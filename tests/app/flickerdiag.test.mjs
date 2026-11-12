// Diagnostic for #520 (the map flickers when a continent, country or state is picked): counts what the map is asked to do after one pick.
import { test } from 'node:test';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  for (const cont of ['Asia', 'Europe']) test(`${name}: ${cont}: map calls after picking a continent (diagnostic, #520)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
    await p.waitForTimeout(1500);
    const counts = await p.evaluate(async (CONT) => {
      const m = window.__M.map, c = {}; const bump = (k) => { c[k] = (c[k] || 0) + 1; };
      for (const fn of ['fitBounds', 'setFilter', 'setPaintProperty', 'setLayoutProperty', 'easeTo', 'flyTo', 'jumpTo', 'setStyle', 'resize']) { const o = m[fn].bind(m); m[fn] = (...a) => { bump(fn + (fn === 'setPaintProperty' || fn === 'setFilter' ? ':' + a[0] : '')); return o(...a); }; }
      for (const id of Object.keys(m.style.sourceCaches || {})) { const s = m.getSource(id); if (s && s.setData) { const o = s.setData.bind(s); s.setData = (d) => { bump('setData:' + id); return o(d); }; } }
      let renders = 0; m.on('render', () => renders++);
      let mo = 0, mv = 0, st = []; new MutationObserver((l) => { mo += l.length; }).observe(document.body, { childList: true, subtree: true }); m.on('moveend', () => mv++); m.on('movestart', () => { st.push(window.__M.sheetState); });
      const btn = true; const cam = []; m.on('move', () => { const ce = m.getCenter(); cam.push(ce.lng.toFixed(0) + ',' + ce.lat.toFixed(0) + ',z' + m.getZoom().toFixed(2)); }); window.__M.go('continent', CONT);
      await new Promise((r) => setTimeout(r, 3000));
      c.renders = renders; c.camFirst = cam.slice(0, 3).join('|'); c.camLast = cam.slice(-2).join('|'); c.moveEvents = cam.length; c.minZoom = m.getMinZoom(); c.mutations = mo; c.moves = mv; c.sheet = st.join('/'); c.size = innerWidth + 'x' + innerHeight + ' mapH=' + m.getContainer().clientHeight; return c;
    }, cont);
    await b.close();
    const tot = {}; for (const [k, v] of Object.entries(counts)) { const g = k.split(':')[0]; tot[g] = (typeof v === 'number' ? (tot[g] || 0) + v : v); }
    throw new Error('DIAG ' + name + ' ' + cont + ' ' + Object.entries(tot).map(([k, v]) => k + '=' + v).join(' '));
  });
}
