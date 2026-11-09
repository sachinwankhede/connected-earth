// Screenshots of key screens at a phone size, for the `screens` workflow (#566). Not a test: it never fails the build, it only writes PNGs to the folder given as the
// first argument (default screens-out/). A screen that cannot be reached is skipped and listed in index.txt. Run after `npm run build`; CI only (no browser in a session).
import fs from 'node:fs';
import path from 'node:path';
import * as H from '../app/helper.mjs';

const out = path.resolve(process.argv[2] || 'screens-out');
fs.mkdirSync(out, { recursive: true });
const size = { width: 390, height: 844 };
const notes = [];
const answered = (p, q) => p.waitForFunction((x) => window.__M && window.__M.searched === x, q, { timeout: 60000 });
const shot = async (p, name) => { await p.waitForTimeout(800); await p.screenshot({ path: path.join(out, name + '.png') }); notes.push('ok   ' + name); };
const step = async (name, fn) => { try { await fn(); } catch (e) { notes.push('skip ' + name + ': ' + String(e.message || e).split('\n')[0].slice(0, 160)); } };

const b = await H.launch();
try {
  await step('home', async () => {
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); await shot(t.page, '01-home');
  });
  await step('species tab', async () => {
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.locator('[data-tab="species"]').first().click({ timeout: 8000 }); await p.waitForSelector('#sptab:not([hidden])', { timeout: 30000 }); await shot(p, '02-species-tab');
  });
  await step('map mode', async () => {
    const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.click('#q'); await p.keyboard.type('osprey'); await p.keyboard.press('Enter'); await answered(p, 'osprey');
    await p.waitForFunction(() => !document.getElementById('qhead').hidden, null, { timeout: 30000 });
    await p.locator('#qhead a[data-hmap]').first().click({ timeout: 8000 });
    await p.waitForFunction(() => document.querySelector('#qhead.qchip') && /in \d+ place/.test(document.getElementById('qhead').textContent), null, { timeout: 30000 });
    await shot(p, '03-map-mode');
    await p.locator('#regions [data-go]').first().click({ timeout: 8000 }); await p.waitForTimeout(1500); await shot(p, '04-map-mode-continent');
  });
} finally { await b.close?.(); }
fs.writeFileSync(path.join(out, 'index.txt'), notes.join('\n') + '\n');
console.log(notes.join('\n'));
process.exit(0);
