import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const template = fs.readFileSync(path.join(ROOT, 'src', 'sw.template.js'), 'utf8');
const source = template.replace('__SPECIES_HOSTS__', '');   // no separate species address (item #692)

function worker(code = source) {
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
  vm.runInNewContext(code, {
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

test('service worker refreshes map style metadata and reuses cached tiles offline and leaves pictures from other sites alone', async () => {
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

  // pictures are our own hosted files now: the worker no longer touches another site's pictures at all
  assert.equal(await sw.request(thumbnail), undefined);
  assert.deepEqual(sw.calls, [style, style]);
});

// item #692: with the species files published at their own address (SPECIES_BASE), the worker keeps those files like the other photo hosts: cache first, usable offline
test('service worker keeps files from the separate species address and still ignores other sites', async () => {
  const sw = worker(template.replace('__SPECIES_HOSTS__', ', "species.example.pages.dev"'));
  const photo = 'https://species.example.pages.dev/photos/species-md/a1b2c3d4e5f6.webp';
  const other = 'https://other.example.com/photos/species-md/a1b2c3d4e5f6.webp';
  assert.equal(await (await sw.request(photo)).text(), `network:${photo}`);
  sw.setOffline(true);
  assert.equal(await (await sw.request(photo)).text(), `network:${photo}`);   // answered from the cache, the network is not asked again
  assert.deepEqual(sw.calls, [photo]);
  assert.equal(await sw.request(other), undefined);
});
