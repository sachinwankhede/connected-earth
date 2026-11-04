// The shipped suggestion ranking (#413) on the built s-<xx>.json files: the code is cut out of src/app/suggest.js and src/app/data.js and run as it is.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const R = new URL('../../', import.meta.url).pathname;
const built = fs.existsSync(R + 'api/search/meta.json');
const cut = (file, name) => { const t = fs.readFileSync(R + file, 'utf8'); const i = t.indexOf('function ' + name + '('); assert.ok(i >= 0, name); const j = t.indexOf('\n  }\n', i); return t.slice(i, j < 0 ? t.indexOf('\n', i) : j + 4); };
const load = () => new Function('max', cut('src/app/data.js', 'srchWords') + cut('src/app/suggest.js', 'sugPick') + 'var sugMax = function () { return max; }; return { srchWords: srchWords, pick: sugPick };');
const file = (k) => JSON.parse(fs.readFileSync(R + 'api/search/s-' + k + '.json', 'utf8'));

test('a species and a place come back for the start of their name; names that start with the text come first', { skip: !built }, () => {
  const { pick } = load()(5);
  const rows = pick('osp', file('os'));
  assert.ok(rows.some((r) => r.t === 's' && r.latin === 'Pandion haliaetus' && r.n > 1), 'osprey with its number of places');
  const starts = rows.map((r) => r.k >> 1);
  assert.deepEqual(starts, [...starts].sort(), 'starts-with before contains');
  assert.ok(rows.every((r) => r.t === 'p' || r.k % 2 === 1));
});

test('at most the wanted number of rows, places before species, and every typed word must start a word of the name', { skip: !built }, () => {
  const { pick } = load()(3);
  const d = file('ye');
  const rows = pick('ye', d);
  assert.ok(rows.length <= 3);
  const seenS = rows.findIndex((r) => r.t === 's'), lastP = rows.map((r) => r.t).lastIndexOf('p');
  if (seenS >= 0 && lastP >= 0 && rows[seenS].k >> 1 === rows[lastP].k >> 1) assert.ok(lastP < seenS, 'places first within the same rank');
  assert.deepEqual(pick('yellowstone zzz', d), [], 'a word that starts no word of the name removes the row');
  assert.deepEqual(pick('', d), []);
});

test('Latin names and accents work', { skip: !built }, () => {
  const { pick } = load()(5);
  assert.ok(pick('pandion', file('pa')).some((r) => r.latin === 'Pandion haliaetus'), 'Latin name');
});
