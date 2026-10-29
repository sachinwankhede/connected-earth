// A state park or refuge with no story shows one plain Wikipedia sentence on its place page; one without a summary shows its blurb (docs/DESIGN.md "Place summary").
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

import fs from 'node:fs';
const sums = JSON.parse(fs.readFileSync(new URL('../pipeline/summaries.json', import.meta.url), 'utf8'));
// the same rule build.py uses: the park's first Wikipedia source names the article
const summaryOf = (e) => { const s = (e.sources || []).find((x) => /^Wikipedia:/.test(x.title)), m = s && /wikipedia\.org\/wiki\/([^#?]+)/.exec(s.url || ''); return (m && sums[decodeURIComponent(m[1]).replace(/_/g, ' ')]) || ''; };
const places = H.readPlaces(true).map((e) => ({ ...e, summary: summaryOf(e) }));
const withSummary = places.filter((e) => e.park && !e.story && e.summary);
const without = places.filter((e) => e.park && !e.story && !e.summary && e.blurb);

for (const [name, size] of Object.entries(H.SIZES)) {
  async function show(id) {
    const b = await H.launch();
    const t = await H.open(b, H.PILOT, size, { hash: '#stub' });
    const errors = []; t.page.on('pageerror', (e) => errors.push(String(e)));
    await t.page.waitForTimeout(500);
    await t.page.evaluate((i) => window.__M.showPlace(i), id);
    await t.page.waitForSelector('#pgraph .pn', { timeout: 60000 });
    const r = await t.page.evaluate(() => { const p = document.querySelector('#pview .pstory'); return { text: p ? p.textContent : null, bold: p ? !!p.querySelector('b') : null, q: !!document.querySelector('#pview .jwhy') }; });
    return { b, r, errors };
  }
  test(`${name}: a park with a summary shows it as plain text, under the picture, with no story lead-in`, async () => {
    if (!Object.keys(sums).length) return;   // nothing fetched yet (the data-about job fills pipeline/summaries.json)
    assert.ok(withSummary.length > 0, 'some parks have a summary');
    for (const e of [withSummary[0], withSummary[withSummary.length - 1]]) {
      const { b, r, errors } = await show(e.id);
      assert.equal(r.text, e.summary); assert.equal(r.bold, false); assert.equal(r.q, false); assert.deepEqual(errors, []); await b.close();
    }
  });
  test(`${name}: a park with no summary falls back to its blurb`, async () => {
    if (!without.length) return;
    const e = without[0], { b, r, errors } = await show(e.id);
    assert.equal(r.text, e.blurb); assert.deepEqual(errors, []); await b.close();
  });
}
