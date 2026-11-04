// The search box on a phone (#409): 16px so iOS does not zoom, a Clear link only while there is text, Enter closes the keyboard.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: search box has a Clear link that empties it, and Enter leaves the box`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.waitForFunction(() => window.__M && window.__M.map, null, { timeout: 60000 });
    const clr = () => p.evaluate(() => !document.getElementById('qclr').hidden);
    assert.equal(await clr(), false, 'no Clear link while the box is empty');
    if (name === 'phone') assert.ok(await p.evaluate(() => parseFloat(getComputedStyle(document.getElementById('q')).fontSize)) >= 16, 'at least 16px so iOS does not zoom');
    assert.equal(await p.evaluate(() => document.getElementById('q').getAttribute('enterkeyhint')), 'search');
    await p.click('#q'); await p.keyboard.type('elk');
    assert.equal(await clr(), true, 'Clear link shows with text');
    const bx = await p.evaluate(() => { const r = document.getElementById('qclr').getBoundingClientRect(); return { w: r.width, h: r.height }; });
    assert.ok(bx.w >= 44 && bx.h >= 44, 'Clear link is at least 44px');
    await p.keyboard.press('Enter');
    assert.equal(await p.evaluate(() => document.activeElement && document.activeElement.id), '', 'Enter leaves the box');
    await p.click('#qclr'); await p.waitForTimeout(300);
    assert.equal(await p.evaluate(() => document.getElementById('q').value), '', 'text cleared');
    assert.equal(await clr(), false, 'Clear link hidden again');
    assert.equal(await p.evaluate(() => document.activeElement.id), 'q', 'focus stays in the box');
    assert.deepEqual(t.errors, []); await b.close();
  });
}
