import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = fs.readFileSync(path.join(ROOT, 'src', 'sw.template.js'), 'utf8');

function worker() {
  const listeners = {};
  const entries = new Map();
  const calls = [];
  let offline = false;
  const cache = {
    match: async (request) => entries.get(request.url)?.clone(),
    put: async (request, response) => entries.set(request.url, response.clone()),
    keys: async () => [...entries.keys()].map((url) => new Request(url)),
    delete: async (request) => entries.delete(request.url),
  };
  const scope = {
    addEventListener: (name, callback) => { listeners[name] = callback; },
  };
  vm.runInNewContext(source, {
    self: scope,
    caches: { open: async () => cache },
    fetch: async (request) => {
      calls.push(request.url);
      if (offline) throw new TypeError('offline');
      return new Response(`network:${request.url}`);
    },
    location: { origin: 'https://connected-earth.test' },
    URL,
    Request,
    console,
  });
  return {
    calls,
    setOffline: (value) => { offline = value; },
    async seed(url, text) { entries.set(url, new Response(text)); },
    async request(url) {
      let response;
      listeners.fetch({
        request: new Request(url),
        respondWith: (promise) => { response = promise; },
      });
      return response;
    },
  };
}

test('service worker refreshes map style metadata and reuses cached tiles and thumbnails offline', async () => {
  const sw = worker();
  const style = 'https://tiles.openfreemap.org/styles/liberty';
  const tile = 'https://tiles.openfreemap.org/planet/0/0/0.pbf';
  const thumbnail = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/example.jpg';
  await sw.seed(style, 'stale style');
  await sw.seed(tile, 'cached tile');

  assert.equal(await (await sw.request(style)).text(), `network:${style}`);
  assert.deepEqual(sw.calls, [style]);

  assert.equal(await (await sw.request(tile)).text(), 'cached tile');
  assert.deepEqual(sw.calls, [style]);

  sw.setOffline(true);
  assert.equal(await (await sw.request(style)).text(), `network:${style}`);
  assert.equal(await (await sw.request(tile)).text(), 'cached tile');
  assert.deepEqual(sw.calls, [style, style]);

  sw.setOffline(false);
  assert.equal(await (await sw.request(thumbnail)).text(), `network:${thumbnail}`);
  assert.deepEqual(sw.calls, [style, style, thumbnail]);
  sw.setOffline(true);
  assert.equal(await (await sw.request(thumbnail)).text(), `network:${thumbnail}`);
  assert.deepEqual(sw.calls, [style, style, thumbnail]);
});
