// The app's search lookup (item #260, step 2) run on the built word index, without a browser: the code is cut out of the built page, so what runs here is what ships.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const R = new URL('../../', import.meta.url).pathname;
const built = fs.existsSync(R + 'index.html') && fs.existsSync(R + 'api/search/meta.json') && fs.existsSync(R + 'api/places/main/index-world.json');

function lookup() {
  const html = fs.readFileSync(R + 'index.html', 'utf8');
  const code = html.match(/  var SRCH = [\s\S]*?\n  \/\* a typed query/)[0].replace(/\n  \/\* a typed query$/, '');
  const rd = (n) => JSON.parse(fs.readFileSync(R + 'api/places/main/' + n + '.json', 'utf8'));
  const ECOS = rd('index-world').concat(rd('index-local'));
  const fetch = (u) => fs.existsSync(R + u) ? Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(R + u, 'utf8'))) }) : Promise.resolve({ ok: false });
  const ECO_BY = Object.fromEntries(ECOS.map((e) => [e.id, e]));   // every place is loaded here (the page loads the local ones before it looks up)
  const Places = { loadLocals: () => Promise.resolve(true), total: ECOS.length };
  const ctx = vm.createContext({ ECOS, ECO_BY, Places, fetch, Promise, Set });
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
  assert.ok(c.SRCH.ok, 'the lookup never gave up');
});
