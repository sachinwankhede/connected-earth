import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as H from './helper.mjs';

test('service worker serves cached data and the app shell offline without substituting HTML for data', async () => {
  const browser = await H.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  try {
    await ctx.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (route) => route.abort());
    const appUrl = new URL(await H.urlFor(H.MAIN));
    appUrl.hostname = 'localhost';
    await page.goto(appUrl.href);
    await page.evaluate(async () => {
      await navigator.serviceWorker.ready;
    });
    await page.waitForFunction(() => !!navigator.serviceWorker.controller);

    const dataUrl = new URL('webs/about.json', appUrl).href;
    const online = await page.evaluate(async (url) => {
      const response = await fetch(url);
      return { ok: response.ok, type: response.headers.get('content-type'), value: await response.json() };
    }, dataUrl);
    assert.equal(online.ok, true);
    assert.match(online.type, /application\/json/);
    assert.ok(online.value && typeof online.value === 'object');

    H.setServerOffline(true);
    await ctx.setOffline(true);
    const offlineData = await page.evaluate(async (url) => {
      const response = await fetch(url);
      return { ok: response.ok, type: response.headers.get('content-type'), value: await response.json() };
    }, dataUrl);
    assert.equal(offlineData.ok, true);
    assert.match(offlineData.type, /application\/json/);
    assert.ok(offlineData.value && typeof offlineData.value === 'object');

    const uncachedData = await page.evaluate(async () => {
      try {
        const response = await fetch('./webs/not-cached.json');
        return { resolved: true, type: response.headers.get('content-type') };
      } catch {
        return { resolved: false };
      }
    });
    assert.deepEqual(uncachedData, { resolved: false });

    const offlineRoute = new URL('offline-route/', appUrl).href;
    await page.goto(offlineRoute);
    assert.equal(new URL(page.url()).pathname.endsWith('/offline-route/'), true);
    await page.waitForSelector('#map', { timeout: 10000 });
  } finally {
    H.setServerOffline(false);
    await ctx.close();
    await browser.close();
  }
});
