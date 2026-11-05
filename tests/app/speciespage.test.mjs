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
    if (file.ph) { await p.waitForFunction(() => { const i = document.querySelector('#pview #sp-img img'), w = document.querySelector('#pview .jphoto'); return (i && i.offsetParent) || (w && w.complete && w.naturalWidth > 0); }, null, { timeout: 30000 }); await p.locator('#pview .srcd summary').click(); assert.match(await p.evaluate(() => document.getElementById('spcredit').textContent), /Species photos: Wikipedia/); }
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
    assert.match(await p.evaluate(() => document.querySelector('#pview .where').textContent), /^(Countries: .+ · )?Continents: .+$/, 'where it lives: countries and continents (#445)');
    assert.match(info.h3.find((x) => /^Found in/.test(x)), /^Found in \d+ places$/); assert.ok(info.rows >= 2 && info.rows <= 10); assert.ok(info.h >= 44, 'rows are tappable'); assert.equal(info.buttons, false, 'links, not buttons');
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

  test(`${name}: the species page lists what it eats and what eats it; a row opens that species and Back says the name (#447)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForSelector('#pview .sgl .sgr[data-latin]', { timeout: 60000 });
    const d = await p.evaluate(() => ({ heads: [...document.querySelectorAll('#pview h3')].map((h) => h.textContent), rows: [...document.querySelectorAll('#pview .sgl .sgr')].map((r) => ({ latin: r.getAttribute('data-latin'), line: r.querySelector('i').textContent, h: r.getBoundingClientRect().height })) }));
    assert.ok(d.heads.some((h) => h === 'What eats it') || d.heads.some((h) => h === 'What it eats'), 'a diet heading: ' + d.heads);
    assert.ok(d.rows.length > 0 && d.rows.length <= 8 && d.rows.every((r) => /^Species · in \d+ places?$/.test(r.line) && r.h >= 44), 'rows look like the Species tab rows');
    assert.ok(!d.rows.some((r) => r.latin === 'Pandion haliaetus'), 'a species is not its own food');
    const first = d.rows[0].latin;
    await p.evaluate(() => document.querySelector('#pview .sgl .sgr').click());
    await p.waitForFunction((l) => document.getElementById('pview').innerHTML.includes(l) || document.querySelector('#pview .jr i') && document.querySelector('#pview .jr i').textContent === l, first, { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ Osprey');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: the species page names its group, order and family, and the group opens its list in the Species tab (#446)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=pandion-haliaetus' }); const p = t.page;
    await p.waitForSelector('#pview .tax a[data-sg]', { timeout: 60000 });
    const tx = await p.evaluate(() => ({ text: document.querySelector('#pview .tax').textContent, g: document.querySelector('#pview .tax a').getAttribute('data-sg') }));
    assert.equal(tx.g, 'birds'); assert.match(tx.text, /^Birds › Accipitriformes › Pandionidae$/);
    await p.evaluate(() => { if (window.__M.setSheet) window.__M.setSheet('half'); });
    await p.evaluate(() => document.querySelector('#pview .tax a').click());
    await p.waitForFunction(() => document.getElementById('pview').hidden && !document.getElementById('sptab').hidden && /^Birds · \d+$/.test((document.querySelector('#sptab h3') || {}).textContent || ''), null, { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#sptab .jback').textContent.trim()), '‹ Species');
    assert.equal(await p.evaluate(() => window.__M.tab), 'species');
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: the species page lists related species of the same family and a row opens that species (#448)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=canis-lupus' }); const p = t.page;
    await p.waitForFunction(() => [...document.querySelectorAll('#pview h3')].some((h) => h.textContent === 'Related species'), null, { timeout: 60000 });
    const d = await p.evaluate(() => { const h = [...document.querySelectorAll('#pview h3')].find((x) => x.textContent === 'Related species'); const rows = [...h.nextElementSibling.querySelectorAll('.sgr')]; return { n: rows.length, latins: rows.map((r) => r.getAttribute('data-latin')), name: document.querySelector('#pview h2').textContent }; });
    assert.ok(d.n >= 1 && d.n <= 5, 'up to five rows: ' + d.n); assert.ok(!d.latins.includes('Canis lupus'), 'not itself');
    await p.evaluate(() => { const h = [...document.querySelectorAll('#pview h3')].find((x) => x.textContent === 'Related species'); h.nextElementSibling.querySelector('.sgr').click(); });
    await p.waitForFunction((l) => document.querySelector('#pview .jr i') && document.querySelector('#pview .jr i').textContent === l, d.latins[0], { timeout: 60000 });
    assert.equal(await p.evaluate(() => document.querySelector('#pview .jback').textContent.trim()), '‹ ' + d.name);
    assert.deepEqual(t.errors, []); await b.close();
  });

  test(`${name}: a species with a larger picture shows it as a wide photo above the title (#421)`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&sp=odocoileus-virginianus' }); const p = t.page;
    await p.waitForFunction(() => { const i = document.querySelector('#pview .jphoto'); return i && i.complete && i.naturalWidth > 0 && document.querySelector('#pview article').classList.contains('bigphoto'); }, null, { timeout: 60000 });
    const d = await p.evaluate(() => { const i = document.querySelector('#pview .jphoto'), r = i.getBoundingClientRect(); return { src: i.src, w: r.width, h: r.height, small: getComputedStyle(document.querySelector('#pview .jhimg')).display, title: document.querySelector('#pview h2').textContent }; });
    assert.match(d.src, /photos\/species-lg\/.+\.webp$/); assert.ok(d.w > 200 && d.h > 100 && d.h <= 262, 'a wide photo: ' + d.w + 'x' + d.h); assert.equal(d.small, 'none', 'the small square is not shown next to it');
    assert.ok(d.title.length > 0);
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

for (const [name, size] of Object.entries(H.SIZES)) {
  test(`${name}: the species sheet of a graph links to the species page and Back returns to the graph`, async () => {
    const b = await H.launch(); const t = await H.open(b, H.MAIN, size, { hash: '#stub&e=npmammothcave' }); const p = t.page;
    await p.waitForSelector('.node', { timeout: 60000 });
    const latin = await p.evaluate(async () => {
      for (const c of [...document.querySelectorAll('.node')]) {
        c.dispatchEvent(new MouseEvent('click', { bubbles: true })); await new Promise((r) => setTimeout(r, 300));
        for (let w = 0; w < 40 && document.getElementById('where-else'); w++) await new Promise((r) => setTimeout(r, 100));
        const a = document.querySelector('#panel [data-spage]'); if (a) return a.getAttribute('data-spage');
      }
      return null;
    });
    assert.ok(latin, 'a species that lives in another place has the link');
    await p.evaluate(() => document.querySelector('#panel [data-spage]').click());
    await p.waitForFunction(() => document.querySelector('#pview h2') && !document.getElementById('pview').hidden, null, { timeout: 60000 });
    const s = await page(p); assert.match(s.hash, /(^|&)sp=[a-z0-9-]+$/); assert.match(s.back, /^‹ \S/); assert.notEqual(s.back, '‹ Places', 'Back names the place it returns to');
    await p.evaluate(() => history.back()); await p.waitForTimeout(1200);
    assert.equal(await p.evaluate(() => !document.getElementById('webview').hidden), true, 'Back returns to the graph');
    assert.match(await p.evaluate(() => decodeURIComponent(location.hash)), /(^|&)e=npmammothcave$/);
    assert.deepEqual(t.errors, []); await b.close();
  });
}
