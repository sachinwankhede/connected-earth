import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

// The world-level places are two files (api/places/main/index-world.json, cards-world.json), not part of the page (#228 step 2, #313 step 3); the local places follow in two more.
const block = (ctx) => ctx.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (route) => route.abort());

test('after one visit the service worker has the world places files, so a reopen without network still lists places', async () => {
  const browser = await H.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  try {
    await block(ctx);
    const appUrl = new URL(await H.urlFor(H.MAIN)); appUrl.hostname = 'localhost';
    await page.goto(appUrl.href);
    await page.evaluate(async () => { await navigator.serviceWorker.ready; });
    await page.waitForFunction(() => !!navigator.serviceWorker.controller);
    await page.waitForSelector('button.card', { state: 'attached', timeout: 20000 });
    const cached = await page.evaluate(async () => {
      const out = [];
      for (const k of await caches.keys()) for (const r of await (await caches.open(k)).keys()) out.push(new URL(r.url).pathname);
      return out;
    });
    for (const f of ['/api/places/main/index-world.json', '/api/places/main/cards-world.json']) assert.ok(cached.includes(f), f + ' is cached');
    H.setServerOffline(true); await ctx.setOffline(true);
    await page.reload();
    await page.waitForSelector('button.card', { state: 'attached', timeout: 20000 });
    assert.ok(await page.evaluate(() => document.querySelectorAll('button.card').length) > 0, 'places are listed offline');
  } finally {
    H.setServerOffline(false); await ctx.close();
  }
});

test('if the places files do not arrive the start screen says so, with a link to try again, and nothing throws', async () => {
  const browser = await H.launch();
  const ctx = await browser.newContext({ serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  try {
    await block(ctx);
    await ctx.route(/api\/places\/main\/cards-world\.json/, (route) => route.fulfill({ status: 500, body: '' }));
    await page.goto(await H.urlFor(H.MAIN));
    await page.waitForFunction(() => /did not load/.test(document.getElementById('boot')?.textContent || ''), null, { timeout: 15000 });
    assert.equal(await page.locator('#boot a').count(), 1);
    assert.deepEqual(errors, []);
  } finally {
    await ctx.close();
  }
});

test('if a place has no card the start screen says the places did not load, instead of showing a place without text', async () => {
  const browser = await H.launch();
  const ctx = await browser.newContext({ serviceWorkers: 'block' });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  try {
    await block(ctx);
    await ctx.route(/api\/places\/main\/cards-world\.json/, (route) => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }));
    await page.goto(await H.urlFor(H.MAIN));
    await page.waitForFunction(() => /did not load/.test(document.getElementById('boot')?.textContent || ''), null, { timeout: 15000 });
    assert.equal(await page.locator('#boot a').count(), 1);
    assert.deepEqual(errors, []);
  } finally {
    await ctx.close();
  }
});

test('if the first cards file does not match the index (an old copy from a cache), the page fetches both again and lists the places (#405)', async () => {
  const browser = await H.launch();
  const ctx = await browser.newContext({ serviceWorkers: 'block' });
  const page = await ctx.newPage();
  try {
    await block(ctx);
    let n = 0;
    await ctx.route(/api\/places\/main\/cards-world\.json/, (route) => {
      n++;
      return n === 1 ? route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }) : route.continue();
    });
    await page.goto(await H.urlFor(H.MAIN));
    await page.waitForSelector('button.card', { state: 'attached', timeout: 20000 });
    assert.equal(n, 2, 'the cards file was asked for twice');
    assert.ok(await page.evaluate(() => document.querySelectorAll('button.card').length) > 0, 'places are listed');
    assert.ok(!(await page.evaluate(() => /did not load/.test(document.getElementById('boot')?.textContent || ''))), 'no error message');
  } finally {
    await ctx.close();
  }
});
