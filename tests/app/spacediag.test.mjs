// Diagnostic for #526/#528: where the vertical space goes on the Species tab and in map mode (phone, sheet half). Fails on purpose to print the numbers.
import { test } from 'node:test';
import * as H from './helper.mjs';

test('phone: layout numbers (diagnostic)', async () => {
  const b = await H.launch(); const t = await H.open(b, H.MAIN, H.SIZES.phone, { hash: '#stub' }); const p = t.page;
  await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
  await p.evaluate(() => window.__M.setSheet && window.__M.setSheet('half'));
  await p.waitForSelector('[data-tab="species"]:visible', { timeout: 60000 });
  const snap = (label) => p.evaluate((l) => {
    const r = (s) => { const e = document.querySelector(s); if (!e) return s + '=none'; const c = getComputedStyle(e), b = e.getBoundingClientRect(); return s + '=' + (c.display === 'none' ? 'hidden' : Math.round(b.top) + '+' + Math.round(b.height) + (e.hidden ? 'H' : '')); };
    return l + ' ' + ['#srow', '#regions', '#qhead', '#cards'].map(r).join(' ');
  }, label);
  const out = [];
  await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter'); await p.waitForTimeout(2500);
  await p.evaluate(() => { const a = document.querySelector('#qhead a[data-hmap]'); if (a) a.click(); }); await p.waitForTimeout(2500);
  out.push(await snap('mm'));
  out.push(await p.evaluate(() => 'regions=' + document.getElementById('regions').children.length + ' first=' + (document.querySelector('#regions .chip') || {}).textContent + ' q=' + document.getElementById('q').value + ' qn=' + document.getElementById('qnote').textContent.slice(0, 30)));
  await b.close();
  throw new Error('DIAG ' + out.join(' || '));
});
