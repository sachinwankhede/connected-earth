// Suggestions while typing (#413): a short dropdown under the search box, at most 3 rows on a phone and 5 on desktop, species rows say how many places,
// a tap on a species row filters the map, Enter / Clear / a tap elsewhere close it.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: typing shows suggestions, a species row runs the species filter, Enter and Clear close them`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    const rows = () => p.evaluate(() => { const s = document.getElementById('sug'); return s.hidden ? [] : [...s.querySelectorAll('.sgr')].map((r) => ({ name: r.querySelector('b').textContent, line: r.querySelector('i').textContent, latin: r.getAttribute('data-latin'), id: r.getAttribute('data-id') })); });
    assert.deepEqual(await rows(), [], 'nothing before typing');
    await p.click('#q'); await p.keyboard.type('o');
    assert.deepEqual(await rows(), [], 'one letter is not enough');
    await p.keyboard.type('sp');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    let r = await rows();
    assert.ok(r.length >= 1 && r.length <= (name === 'phone' ? 3 : 5), 'row count');
    const osprey = r.find((x) => x.latin === 'Pandion haliaetus');
    assert.ok(osprey, 'osprey is suggested for "osp"');
    assert.match(osprey.line, /^Species · in \d+ places$/);
    const hit = await p.evaluate(() => { const b = document.querySelector('#sug .sgr').getBoundingClientRect(); return b.height; });
    assert.ok(hit >= 44, 'rows are at least 44px tall');
    await p.keyboard.press('Enter');
    assert.deepEqual(await rows(), [], 'Enter closes the suggestions');
    await p.click('#qclr'); await p.keyboard.type('osp');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    await p.click('#sug .sgr[data-latin="Pandion haliaetus"]');
    await p.waitForTimeout(500);
    assert.deepEqual(await rows(), [], 'a tap on a row closes the suggestions');
    assert.equal(await p.evaluate(() => document.getElementById('q').value), 'Osprey', 'the box shows the species');
    await p.click('#q'); await p.keyboard.type('x'); await p.waitForTimeout(200);
    await p.click('#qclr'); await p.waitForTimeout(200);
    assert.deepEqual(await rows(), [], 'Clear closes the suggestions');
    // every row says its type (#424): a place "Place · <state or country>", a species "Species · in N places"
    await p.click('#q'); await p.keyboard.type('yellowst');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    r = await rows();
    const yp = r.find((x) => x.id === 'yellowstone');
    assert.ok(yp, 'Greater Yellowstone is suggested for "yellowst"');
    assert.match(yp.line, /^Place · .+/, 'a place row names the state or country');
    assert.ok(r.every((x) => /^Place( · .+)?$/.test(x.line) || /^Species · in \d+ places?$/.test(x.line)), 'no row without a type');
    // the whole name typed comes first (#424)
    await p.click('#qclr'); await p.keyboard.type('osprey');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    r = await rows();
    assert.equal(r[0].latin, 'Pandion haliaetus', 'the species named exactly "Osprey" is the first row');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
