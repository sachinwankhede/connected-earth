// Cards must never show a missing value: a field removed from the page data shows up here as "undefined", "NaN" or "null" in the card text.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

await H.fixtureBuild();   // the fixture build (#787): a change to the real data cannot reach this file

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: no place card shows a missing value, and each shows its species and feeding-link counts`, async () => {
    const b = await H.launch();
    const t = await H.open(b, H.FMAIN, size, { hash: '#stub' });
    const p = t.page;
    await p.waitForSelector('#cards .card', { state: 'attached', timeout: 60000 });
    // ask for more cards where the list is paged (phone), so the later cards are checked too
    for (let i = 0; i < 4; i++) { await p.evaluate(() => { const m = document.getElementById('more'); if (m && !m.closest('[hidden]')) m.click(); }); await H.pause(p, 150); }
    const r = await p.evaluate(() => {
      const cards = [...document.querySelectorAll('#cards li:not([hidden]):not(.pg) .card')];
      const bad = cards.filter((c) => /undefined|NaN|null/.test(c.textContent)).map((c) => c.getAttribute('data-eco'));
      const noCount = cards.filter((c) => !/\d+ species · \d+ feeding links/.test(c.textContent)).map((c) => c.getAttribute('data-eco'));
      return { n: cards.length, bad, noCount };
    });
    assert.ok(r.n >= 10, 'cards are shown: ' + r.n);
    assert.deepEqual(r.bad, [], 'cards with a missing value');
    assert.deepEqual(r.noCount, [], 'cards without counts');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
