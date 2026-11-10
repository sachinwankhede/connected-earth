// Screenshots of screens at a phone size, for the `screens` workflow (#566). Not a test: it never fails the build, it writes PNGs and index.txt to the folder given as the
// first argument (default screens-out/). Run after `npm run build`; CI only (no browser in a session).
// RULE: a pull request that changes a screen adds or updates that screen's scenario below in the same pull request (like a test), so the picture that comes back shows the change.
// A scenario that cannot be reached is listed as "skip" in index.txt and in the pull request comment, so a missing picture is noticed and not silent.
import fs from 'node:fs';
import path from 'node:path';
import * as H from '../app/helper.mjs';

const out = path.resolve(process.argv[2] || 'screens-out');
fs.mkdirSync(out, { recursive: true });
const size = { width: 390, height: 844 };
const answered = (p, q) => p.waitForFunction((x) => window.__M && window.__M.searched === x, q, { timeout: 60000 });
const searchFor = async (p, q) => { await p.click('#q'); await p.keyboard.type(q); await p.keyboard.press('Enter'); await answered(p, q); };
const open = async (b) => (await H.open(b, H.MAIN, size, { hash: '#stub' })).page;

// name -> what it shows (for the comment) and the steps; shot(label) takes a picture named <scenario>-<label>.
export const SCENARIOS = {
  'home': { shows: 'the start screen with the sheet', run: async (p, shot) => { await shot(''); } },
  'search-results': { shows: 'a search for "osprey": the result header and the list', run: async (p, shot) => {
    await searchFor(p, 'osprey'); await p.waitForFunction(() => !document.getElementById('qhead').hidden, null, { timeout: 30000 }); await shot(''); } },
  'map-mode': { shows: '"Show on the map" from a species (title row, close, pills), then a continent, a country and, where there is one, a state picked (the one pill row: back pill, All pill, children)', run: async (p, shot) => {
    await searchFor(p, 'osprey'); await p.waitForFunction(() => !document.getElementById('qhead').hidden, null, { timeout: 30000 });
    await p.locator('#qhead a[data-hmap]').first().click({ timeout: 8000 });
    await p.waitForFunction(() => document.querySelector('#qhead.qchip') && /in \d+ place/.test(document.getElementById('qhead').textContent), null, { timeout: 30000 });
    await shot('world'); await p.locator('#regions [data-go]').first().click({ timeout: 8000 }); await p.waitForTimeout(1500); await shot('continent');
    const kid = () => p.locator('#regions [data-go]:not(.leadg *)').first();
    await kid().click({ timeout: 8000 }); await p.waitForTimeout(1500); await shot('country');
    if (await kid().count()) { await kid().click({ timeout: 8000 }); await p.waitForTimeout(1500); await shot('state'); } } },
  'places-regions': { shows: 'the Places tab with no search, sheet open: world, then a continent, a country and a US state picked from the pill row (no title line; the pill row starts with the back pill and the All pill), and the continent again with the sheet collapsed (the trail line)', run: async (p, shot) => {
    const ready = () => p.waitForFunction(() => { const e = document.getElementById('boot'); const c = e && getComputedStyle(e); return (!e || c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) && document.querySelectorAll('#regions [data-go]').length > 0 && document.querySelectorAll('#cards .card').length > 0; }, null, { timeout: 60000 });
    const kid = () => p.locator('#regions [data-go]:not(.leadg *)').first();   // a child pill, not the back pill
    const half = async () => { await p.evaluate(() => window.__M.setSheet('half')); await p.waitForTimeout(600); };
    const pick = async () => { await kid().click({ timeout: 4000 }).catch(() => p.evaluate(() => [...document.querySelectorAll('#regions [data-go]')].find((x) => !x.closest('.leadg')).click())); await p.waitForTimeout(1500); await ready(); await half(); };
    await ready(); await half(); await shot('world');
    await pick(); await shot('continent');
    await pick(); await shot('country');
    if (await kid().count()) { await pick(); await shot('state'); }
    await p.evaluate(() => window.__M.go('continent', 'Africa')); await p.waitForTimeout(1200); await ready(); await p.evaluate(() => window.__M.setSheet('min')); await p.waitForTimeout(600); await shot('collapsed'); } },
  'species-tab': { shows: 'the Species tab: the most common species and the groups', run: async (p, shot) => {
    await p.locator('#tab-species').click({ timeout: 4000 }).catch(() => p.evaluate(() => document.getElementById('tab-species').click()));
    await p.waitForSelector('#sptab:not([hidden])', { timeout: 30000 }); await shot(''); } },
  'species-orders': { shows: 'a group with several orders opened: the one row of order pills', run: async (p, shot) => {
    await p.locator('#tab-species').click({ timeout: 4000 }).catch(() => p.evaluate(() => document.getElementById('tab-species').click()));
    await p.waitForFunction(() => document.querySelectorAll('#regions [data-spg]').length > 0, null, { timeout: 60000 });
    const g = await p.evaluate(() => fetch('api/species-tab/groups.json').then((r) => r.json()).then((a) => (a.find((x) => x[4] > 1) || [])[0]));
    await p.evaluate((k) => document.querySelector('#regions [data-spg="' + k + '"]').click(), g);
    await p.waitForFunction(() => document.querySelector('#regions [data-spo]'), null, { timeout: 60000 }); await shot(''); } },
  'place-sheet': { shows: 'an opened place (Yellowstone)', run: async (p, shot) => {
    await p.evaluate(() => window.__M.showPlace('yellowstone')); await p.waitForTimeout(2500); await shot(''); } },
  'journeys': { shows: 'the Journeys tab', run: async (p, shot) => {
    await p.locator('#tab-journeys').click({ timeout: 4000 }).catch(() => p.evaluate(() => document.getElementById('tab-journeys').click()));
    await p.waitForSelector('#xcards li', { timeout: 30000 }); await shot(''); } },
};

const notes = [], only = (process.argv[3] || '').split(',').filter(Boolean);
const b = await H.launch();
try {
  for (const [name, sc] of Object.entries(SCENARIOS)) {
    if (only.length && !only.includes(name)) continue;
    // a picture counts only when the loading screen (#boot) is gone; a scenario that fails or shows it is tried once more, then listed as skipped
    const bootGone = (p) => p.waitForFunction(() => { const e = document.getElementById('boot'); if (!e) return true; const c = getComputedStyle(e); return c.visibility === 'hidden' || c.display === 'none' || +c.opacity === 0; }, null, { timeout: 20000 });
    let err = null;
    for (let attempt = 0; attempt < 2; attempt++) {
      const got = [];
      try {
        const p = await open(b); await bootGone(p);
        await sc.run(p, async (label) => { await bootGone(p); await p.waitForTimeout(800); const f = name + (label ? '-' + label : ''); await p.screenshot({ path: path.join(out, f + '.png') }); got.push('ok   ' + f + '  (' + sc.shows + ')'); });
        notes.push(...got); err = null; break;
      } catch (e) { err = 'skip ' + name + ': ' + String(e.message || e).split('\n')[0].slice(0, 160); }
      await b.close?.();   // each attempt gets a fresh context
    }
    if (err) notes.push(err);
    await b.close?.();
  }
} finally { await b.close?.(); }
fs.writeFileSync(path.join(out, 'index.txt'), notes.join('\n') + '\n');
console.log(notes.join('\n'));
process.exit(0);
