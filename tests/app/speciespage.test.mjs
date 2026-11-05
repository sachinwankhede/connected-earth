// The species page (#420 step 1): names, kind line, picture or placeholder, description, share, credits; it has its own address (sp=<latin slug>) and Back leaves it.
// A species with no file, no description or no picture still shows what it has.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

const page = (p) => p.evaluate(() => {
  const g = (s) => { const e = document.querySelector('#pview ' + s); return e ? e.textContent.trim() : null; };
  return { hidden: document.getElementById('pview').hidden, name: g('h2'), latin: g('.jr'), kind: g('.jkind'), about: g('.about'), back: g('.jback'), img: !!document.querySelector('#pview #sp-img img'), share: !!document.querySelector('#pview .shbtn'), foot: !!document.querySelector('#pview .srcd'), hash: decodeURIComponent(location.hash), map: !document.getElementById('mapview').hidden };
});

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: a species page shows its names, kind, description, picture, share and credits, and Back leaves it`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    const file = await p.evaluate(() => fetch('api/species/pandion-haliaetus.json').then((r) => r.json()));
    let s = await page(p);
    assert.equal(s.hidden, false); assert.equal(s.name, 'Osprey'); assert.equal(s.latin, 'Pandion haliaetus');
    assert.match(s.kind, /^(Top predator|Hunter & scavenger|Plant-eater|Plant)$/);
    assert.ok(s.about && s.about.length > 40 && /Wikipedia$/.test(s.about), 'the description and its Wikipedia link');
    assert.equal(s.back, '‹ Places'); assert.equal(s.share, true); assert.equal(s.foot, true);
    assert.match(s.hash, /(^|&)sp=pandion-haliaetus$/, 'the species is in the address');
    if (file.ph) { await p.waitForSelector('#pview #sp-img img', { timeout: 30000 }); await p.locator('#pview .srcd summary').click(); assert.match(await p.evaluate(() => document.getElementById('spcredit').textContent), /Species photos: Wikipedia/); }
    await p.reload(); await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    await p.click('.jback'); await p.waitForTimeout(500);
    s = await page(p); assert.equal(s.hidden, true, 'Back closes the page'); assert.equal(s.map, true); assert.doesNotMatch(s.hash, /sp=/);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: from a search the link says Search and the address keeps both; a species with no file or no description or picture still renders`, async () => {
    let b = await H.launch(); let t = await H.open(b, H.MAIN, size, { hash: '#stub&s=osprey&sp=pandion-haliaetus' }); let p = t.page;
    await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview h2').textContent === 'Osprey', null, { timeout: 60000 });
    let s = await page(p); assert.equal(s.back, '‹ Search'); assert.match(s.hash, /(^|&)s=osprey&sp=pandion-haliaetus$/);
    await p.click('.jback'); await p.waitForTimeout(600);
    s = await page(p); assert.equal(s.map, true); assert.equal(await p.evaluate(() => document.getElementById('q').value), 'osprey', 'the search is still there');
    assert.deepEqual(t.errors, []); await b.close();
    // no file at all: the name made from the address, no description, the placeholder
    b = await H.launch(); t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=no-such-species' }); p = t.page;
    await p.waitForSelector('#pview h2', { timeout: 60000 }); await p.waitForTimeout(800);
    s = await page(p); assert.equal(s.name, 'No such species'); assert.equal(s.about, null); assert.equal(s.img, false); assert.equal(s.foot, true);
    await b.close();
    // a file with a name and no description and no picture
    b = await H.launch(); t = await H.open(b, H.MAIN, size, { hash: '#stub' }); p = t.page;
    await p.route(/api\/species\/test-bird\.json/, (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ l: 'Testus avis', n: 'Test bird', tl: 3 }) }));
    await p.evaluate(() => { location.hash = '#stub&sp=test-bird'; }); await p.waitForFunction(() => document.querySelector('#pview h2') && document.querySelector('#pview .jr') && document.querySelector('#pview .jr').textContent === 'Testus avis', null, { timeout: 60000 });
    s = await page(p); assert.equal(s.latin, 'Testus avis'); assert.equal(s.kind, 'Hunter & scavenger'); assert.equal(s.about, null); assert.equal(s.img, false);
    await b.close();
  });
}

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: a species page lists its places as rows, a row opens the place and Back returns, and Show on the map filters the map`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&s=osprey&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForSelector('#pview .pj[data-spp]', { timeout: 60000 });
    const info = await p.evaluate(() => ({ h3: [...document.querySelectorAll('#pview h3')].map((h) => h.textContent), rows: document.querySelectorAll('#pview .pj[data-spp]').length, h: document.querySelector('#pview .pj').getBoundingClientRect().height, buttons: document.querySelectorAll('#pview .pj, #pview [data-spmap]').length && [...document.querySelectorAll('#pview .pj, #pview [data-spmap]')].some((e) => e.tagName === 'BUTTON') }));
    assert.match(info.h3[0], /^Found in \d+ places$/); assert.ok(info.rows >= 2 && info.rows <= 10); assert.ok(info.h >= 44, 'rows are tappable'); assert.equal(info.buttons, false, 'links, not buttons');
    const id = await p.evaluate(() => document.querySelector('#pview .pj[data-spp]').getAttribute('data-spp'));
    await p.locator('#pview .pj[data-spp]').first().click({ timeout: 5000 }).catch(() => p.evaluate(() => document.querySelector('#pview .pj[data-spp]').click()));
    await p.waitForFunction(() => document.querySelector('#pview .jhero h2') && !document.querySelector('#pview [data-spmap]'), null, { timeout: 60000 });
    let s = await page(p); assert.match(s.hash, new RegExp('(^|&)s=osprey&pg=' + id + '$'), 'the place is in the address'); assert.equal(s.back, '‹ Places');
    await p.evaluate(() => history.back()); await p.waitForSelector('#pview .pj[data-spp]', { timeout: 60000 });
    s = await page(p); assert.equal(s.name, 'Osprey', 'Back returns to the species page'); assert.match(s.hash, /sp=pandion-haliaetus$/);
    await p.evaluate(() => document.querySelector('#pview [data-spmap]').click()); await p.waitForTimeout(1200);
    s = await page(p); assert.equal(s.hidden, true, 'the page is gone'); assert.equal(s.map, true);
    assert.equal(await p.evaluate(() => document.getElementById('q').value), 'Osprey', 'the map is filtered to the species');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a species found in one place shows that place`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub' }); const p = t.page;
    await p.route(/api\/species-places\/te\.json/, (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ 'Testus avis': ['yellowstone'] }) }));
    await p.route(/api\/species\/testus-avis\.json/, (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ l: 'Testus avis', n: 'Test bird', tl: 3 }) }));
    await p.evaluate(() => { location.hash = '#stub&sp=testus-avis'; });
    await p.waitForSelector('#pview .pj[data-spp="yellowstone"]', { timeout: 60000 });
    assert.match(await p.evaluate(() => document.querySelector('#pview h3').textContent), /^Found in 1 place$/);
    assert.deepEqual(t.errors, []); await b.close();
  });
}
