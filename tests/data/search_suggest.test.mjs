// The shipped suggestion ranking (#413, #424) on the built s-<xx>.json files: the code is cut out of src/app/suggest.js and src/app/data.js and run as it is.
// The ordering rules are checked on small made-up files (a place called "Osprey Lake" does not exist in the data); the real files check that real names come back.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const R = new URL('../../', import.meta.url).pathname;
const built = fs.existsSync(R + 'api/search/meta.json');
const cut = (file, name) => { const t = fs.readFileSync(R + file, 'utf8'); const i = t.indexOf('function ' + name + '('); assert.ok(i >= 0, name); const j = t.indexOf('\n  }\n', i); return t.slice(i, j < 0 ? t.indexOf('\n', i) : j + 4); };
const load = () => new Function('max', cut('src/app/data.js', 'srchWords') + cut('src/app/suggest.js', 'sugPick') + 'var sugMax = function () { return max; }; return { srchWords: srchWords, pick: sugPick };');
const file = (k) => JSON.parse(fs.readFileSync(R + 'api/search/s-' + k + '.json', 'utf8'));
const names = (rows) => rows.map((r) => r.name);

test('a species comes back for the start of its name, with its number of places; ranks never go backwards', { skip: !built }, () => {
  const { pick } = load()(5);
  const rows = pick('osp', file('os'));
  assert.ok(rows.some((r) => r.t === 's' && r.latin === 'Pandion haliaetus' && r.n > 1), 'osprey with its number of places');
  const ks = rows.map((r) => r.k);
  assert.deepEqual(ks, [...ks].sort(), 'exact, then starts-with, then contains');
  assert.ok(rows.every((r) => [0, 1, 2].includes(r.k)));
});

test('the whole name typed comes first, whatever the type (#424)', () => {
  const { pick } = load()(5);
  const d = { p: [['osprey-lake', 'Osprey Lake'], ['osprey-bay', 'Osprey']], s: [['Pandion haliaetus', 'Osprey', 35], ['Pandion cristatus', 'Eastern osprey', 3]] };
  assert.deepEqual(names(pick('osprey', d)), ['Osprey', 'Osprey', 'Osprey Lake', 'Eastern osprey'], 'exact names, then starts-with, then a word that starts with it');
  const rows = pick('osprey', d);
  assert.deepEqual(rows.map((r) => r.k), [0, 0, 1, 2]);
  // a species is not ranked above a place just for being a species, and the other way round
  const e = pick('osprey', { p: [['osprey-lake', 'Osprey Lake']], s: [['Pandion haliaetus', 'Osprey', 35]] });
  assert.deepEqual(e.map((r) => r.t), ['s', 'p'], 'the osprey beats Osprey Lake');
  const f = pick('osprey', { p: [['osprey', 'Osprey']], s: [['Pandion haliaetus', 'Osprey Hawk', 35]] });
  assert.deepEqual(f.map((r) => r.t), ['p', 's'], 'a place named exactly beats a longer species name');
  // the Latin name counts too, and so does a Latin name that is only the start
  const l = pick('pandion haliaetus', { p: [], s: [['Pandion haliaetus', 'Osprey', 35], ['Pandion haliaetus carolinensis', 'American osprey', 2]] });
  assert.deepEqual(l.map((r) => r.latin), ['Pandion haliaetus', 'Pandion haliaetus carolinensis']);
  assert.deepEqual(l.map((r) => r.k), [0, 1]);
});

test('within one rank the better known first, and places and species take turns (#424)', () => {
  const { pick } = load()(8);
  const d = { p: [['p1', 'Elk A'], ['p2', 'Elk B'], ['p3', 'Elk C']], s: [['S one', 'Elk X', 50], ['S two', 'Elk Y', 20]] };
  assert.deepEqual(names(pick('elk', d)), ['Elk A', 'Elk X', 'Elk B', 'Elk Y', 'Elk C'], 'best place, best species, second place, second species, ...');
  // the order inside a kind is the order of the file (home-list order for places, most places first for species)
  assert.deepEqual(pick('elk', d).filter((r) => r.t === 'p').map((r) => r.id), ['p1', 'p2', 'p3']);
  assert.deepEqual(pick('elk', d).filter((r) => r.t === 's').map((r) => r.n), [50, 20]);
  // a worse rank never jumps ahead because it is better known
  const m = pick('elk', { p: [['p1', 'Big Elk'], ['p2', 'Elk Lake']], s: [] });
  assert.deepEqual(names(m), ['Elk Lake', 'Big Elk']);
});

test('at most the wanted number of rows and every typed word must start a word of the name', { skip: !built }, () => {
  const { pick } = load()(3);
  const d = file('ye');
  const rows = pick('ye', d);
  assert.ok(rows.length <= 3);
  assert.deepEqual(pick('yellowstone zzz', d), [], 'a word that starts no word of the name removes the row');
  assert.deepEqual(pick('', d), []);
  assert.equal(load()(2).pick('elk', { p: [['a', 'Elk A'], ['b', 'Elk B']], s: [['S', 'Elk C', 9]] }).length, 2);
});

test('Latin names and accents work', { skip: !built }, () => {
  const { pick } = load()(5);
  assert.ok(pick('pandion', file('pa')).some((r) => r.latin === 'Pandion haliaetus'), 'Latin name');
});
