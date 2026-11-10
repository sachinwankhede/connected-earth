// The app's search lookup (item #260, step 2) run on the built word index, without a browser: the code is cut out of the built page, so what runs here is what ships.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const R = new URL('../../', import.meta.url).pathname;
const built = fs.existsSync(R + 'index.html') && fs.existsSync(R + 'api/search/meta.json') && fs.existsSync(R + 'api/places/main/index-world.json');

function lookup(fetchOverride) {
  const html = fs.readFileSync(R + 'index.html', 'utf8');
  const dataCode = html.match(/  var Data = \(function \(\) \{[\s\S]*?\n  \}\)\(\);/)[0];   // the app's Data module: the lookup reads its files through it
  const code = dataCode + '\n' + html.match(/  var SRCH = [\s\S]*?\n  \/\* a typed query/)[0].replace(/\n  \/\* a typed query$/, '');
  const rd = (n) => JSON.parse(fs.readFileSync(R + 'api/places/main/' + n + '.json', 'utf8'));
  const ECOS = rd('index-world').concat(rd('index-local'));
  let fetch = (u) => fs.existsSync(R + u) ? Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(R + u, 'utf8'))) }) : Promise.resolve({ ok: false });
  const ECO_BY = Object.fromEntries(ECOS.map((e) => [e.id, e]));   // every place is loaded here (the page loads the local ones before it looks up)
  const Places = { loadLocals: () => Promise.resolve(true), total: ECOS.length };
  if (fetchOverride) fetch = fetchOverride;
  const ctx = vm.createContext({ ECOS, ECO_BY, Places, fetch, Promise, Set, Date, location: { pathname: '/' }, window: { fetch } });
  vm.runInContext(code + ';this.srchRun = srchRun; this.SRCH = SRCH;', ctx);
  return ctx;
}

test('typed words find places through the word index', { skip: !built && 'build has not run' }, async () => {
  const c = lookup();
  const ids = async (q) => { const h = await c.srchRun(q); return h && [...h]; };
  assert.deepEqual(await ids('yellowstone'), ['yellowstone'], 'a place name');
  assert.ok((await ids('osprey')).length > 5, 'an animal name found through the species words');
  assert.ok((await ids('ursus arctos')).includes('yellowstone'), 'two words must both match');
  assert.deepEqual(await ids('zzzzq'), [], 'no match is an empty list, not an error');
  assert.equal(await ids('a'), null, 'one letter: no lookup, the page filters on card text');
  assert.ok((await ids('yellowst')).includes('yellowstone'), 'a word prefix matches');
  assert.equal(c.SRCH.failedAt, 0, 'the lookup never failed');
});

test('plurals and spelling pairs find places through the index (#602)', { skip: !built && 'build has not run' }, async () => {
  const c = lookup();
  const ids = async (q) => [...(await c.srchRun(q))].sort();
  const wolf = await ids('wolf'), wolves = await ids('wolves');
  assert.ok(wolves.includes('yellowstone'), 'an irregular plural finds a place with the gray wolf');
  assert.ok(wolves.every((i) => wolf.includes(i)), 'and only places the singular finds too');
  const grey = await ids('grey wolf'), gray = await ids('gray wolf');
  assert.ok(grey.includes('yellowstone') && grey.every((i) => gray.includes(i)), 'a spelling pair finds the places the usual spelling finds (a prefix like gray also matches grayling, so not the other way round)');
  const ospreys = await ids('ospreys');
  assert.ok(ospreys.length > 5, 'a regular plural finds places');
  const osprey = await ids('osprey');
  assert.ok(ospreys.every((i) => osprey.includes(i)), 'a regular plural finds places the singular finds');
  assert.equal(c.SRCH.failedAt, 0);
});

test('a failed lookup is tried again after 30 s, not given up for the session', { skip: !built && 'build has not run' }, async () => {
  let down = true, calls = 0;
  const disk = (u) => fs.existsSync(R + u) ? Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(R + u, 'utf8'))) }) : Promise.resolve({ ok: false });
  const c = lookup((u) => { calls++; return down ? Promise.reject(new Error('offline')) : disk(u); });
  assert.equal(await c.srchRun('yellowstone'), null, 'offline: no hits, the page uses card text');
  assert.ok(c.SRCH.failedAt > 0);
  const n = calls;
  assert.equal(await c.srchRun('yellowstone'), null);
  assert.equal(calls, n, 'within 30 s nothing is fetched again');
  down = false; c.SRCH.failedAt = Date.now() - 31000;
  assert.deepEqual([...(await c.srchRun('yellowstone'))], ['yellowstone'], 'after the cooldown the index works again');
});
