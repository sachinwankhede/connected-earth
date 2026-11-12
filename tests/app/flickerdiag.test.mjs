// Diagnostic for #520 (the map flickers only when Asia is picked): clicks the continent the way a person does and logs every camera call with the code that made it.
import { test } from 'node:test';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  for (const cont of ['Asia', 'Oceania']) test(`${name}: ${cont}: camera calls after clicking the continent (diagnostic, #520)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 60000 });
    await p.waitForTimeout(1500);
    const out = await p.evaluate(async (CONT) => {
      const m = window.__M.map, log = [], t0 = performance.now();
      const who = () => ((new Error().stack || '').split('\n').slice(3, 7).map((l) => (l.trim().match(/at (?:\w+\.)*(\w+)/) || [0, '?'])[1]).filter((x) => !/^(Map|_fitInternal|fitBounds|flyTo|easeTo|jumpTo|_?ease|anonymous|\?)$/.test(x)).slice(0, 2).join('<'));
      for (const fn of ['fitBounds', 'easeTo', 'flyTo', 'jumpTo']) { const o = m[fn].bind(m); m[fn] = (...a) => { if (fn !== 'flyTo') log.push(Math.round(performance.now() - t0) + 'ms ' + fn[0] + ':' + who()); return o(...a); }; }
      m.on('moveend', () => log.push(Math.round(performance.now() - t0) + ' end'));
      const btn = document.querySelector('[data-go="continent"][data-a="' + CONT + '"]');
      if (!btn) return ['no button; data-go found: ' + [...document.querySelectorAll('[data-go]')].slice(0, 6).map((e) => e.dataset.go + ':' + e.dataset.a).join(',')];
      btn.click();
      await new Promise((r) => setTimeout(r, 5000));
      return log;
    }, cont);
    await b.close();
    throw new Error('DIAG ' + name[0] + cont[0] + ' ' + out.join(' '));
  });
}
