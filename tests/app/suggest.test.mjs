// Suggestions while typing (#413): a short dropdown under the search box, at most 3 rows on a phone and 5 on desktop, species rows say how many places,
// a tap on a species row opens the species page (#420 step 3), Enter / Clear / a tap elsewhere close it.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: typing shows suggestions, a species row opens the species page, Enter and Clear close them`, async () => {
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
    await p.click('#q'); await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    await p.evaluate(() => document.getElementById('q').dispatchEvent(new Event('search')));   // the keyboard's search or check key on a phone (#512)
    assert.deepEqual(await rows(), [], 'the search key closes the suggestions');
    assert.equal(await p.evaluate(() => document.activeElement.id), '', 'and the keyboard leaves');
    await p.click('#qclr'); await p.keyboard.type('osp');
    await p.waitForFunction(() => !document.getElementById('sug').hidden, null, { timeout: 15000 });
    await p.click('#sug .sgr[data-latin="Pandion haliaetus"]');
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    assert.deepEqual(await rows(), [], 'a tap on a row closes the suggestions');
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ Search', 'a species row opens its page (#420 step 3)');
    await p.evaluate(() => history.back());
    await p.waitForFunction(() => document.getElementById('q').value === 'osp', null, { timeout: 15000 }).catch(() => {});   // wait for Back to restore the text instead of a fixed pause: a slow runner took longer than 800 ms
    assert.equal(await p.evaluate(() => document.getElementById('q').value), 'osp', 'Back returns to the search that was typed');
    await p.click('#q'); await p.keyboard.type('x'); await p.waitForTimeout(200);
    await p.click('#qclr'); await p.waitForTimeout(200);
    r = await rows();   // the box is empty and focused: the dropdown now lists the recent searches (#589), each marked as one, and no ordinary suggestion
    assert.ok(r.length >= 1 && r.every((x) => /^Recent · /.test(x.line)), 'Clear closes the suggestions and shows the recent searches instead: ' + JSON.stringify(r));
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
