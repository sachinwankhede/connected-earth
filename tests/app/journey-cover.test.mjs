import { createRequire } from 'node:module';
import { test } from 'node:test';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const R = require('../../src/photo-registry.js');

// The cover of a journey by journey id (owner, 15 Nov: "Own"): jpic/jpicm in api/species-pictures.json. Without a row a journey has no cover (#973 phase 4: the title picture is no longer a fallback).
const BASE = 'photos/journeys/';
const credit = { a: 'Ann', l: 'CC BY 4.0', lu: 'https://creativecommons.org/licenses/by/4.0/', p: 'https://commons.wikimedia.org/wiki/File:A.jpg' };
const journey = { id: 'osprey-route', imgwiki: 'Osprey' };

function register(photos, key, value) { R.register(photos, key, R.speciesCandidate(value, value[1], 1, credit)); }
function world() {
  const photos = {};
  register(photos, 'Osprey', ['aaaaaaaaaaaa.webp', 'Osprey']);
  register(photos, 'Place A', ['bbbbbbbbbbbb.webp', 'Place_A']);
  register(photos, 'Place B', ['bbbbbbbbbbbb.webp', 'Place_B']);   // the same file as Place A
  register(photos, 'Place C', ['cccccccccccc.webp', 'Place_C']);
  return photos;
}

test('journeyCandidate builds the file address from the base and the credit from jpicm', () => {
  const c = R.journeyCandidate(['osprey-route.webp', 'Osprey'], BASE, credit);
  assert.equal(c.assetUrl, 'photos/journeys/osprey-route.webp');
  assert.equal(c.sourcePageUrl, 'https://en.wikipedia.org/wiki/Osprey');
  assert.equal(c.author, 'Ann');
  assert.equal(R.journeyCandidate(['osprey-route.webp', 'https://en.wikipedia.org/wiki/Osprey'], BASE, null).sourcePageUrl, 'https://en.wikipedia.org/wiki/Osprey');
});

test('journeyCandidate refuses anything that is not a plain hosted .webp name', () => {
  for (const bad of [['../x.webp', 'p'], ['a/b.webp', 'p'], ['x.jpg', 'p'], [null, 'p'], 'x.webp', null, []]) assert.equal(R.journeyCandidate(bad, BASE, null), null);
  assert.equal(R.journeyCandidate(['x.webp', 'p'], null, null), null);
});

test('no jpic: the journey has no cover, whatever picture its title has; the credits are the end places only', () => {
  const p = world();
  assert.equal(R.coverPhoto(p, journey), null);
  assert.deepEqual(R.coverCredits(p, journey, ['Place A', 'Place C']), [p['Place A'], p['Place C']]);
});

test('jpic row: the cover is the journey\'s own picture with its own credit; the ends stay the place pictures', () => {
  const p = world();
  R.register(p, R.coverKey(journey.id), R.journeyCandidate(['osprey-route.webp', 'Osprey'], BASE, { a: 'Bo', l: 'CC0', p: 'https://commons.wikimedia.org/wiki/File:B.jpg' }));
  assert.equal(R.coverPhoto(p, journey).src, 'photos/journeys/osprey-route.webp');
  assert.equal(R.coverPhoto(p, journey).credit.a, 'Bo');
  assert.deepEqual(R.coverCredits(p, journey, ['Place A', 'Place C']).map(x => x.src),
    ['photos/journeys/osprey-route.webp', p['Place A'].src, p['Place C'].src]);
});

test('credits list each picture once (same src), and the cover once when an end shares it', () => {
  const p = world();
  R.register(p, R.coverKey(journey.id), R.journeyCandidate(['osprey-route.webp', 'Osprey'], BASE, null));
  assert.equal(R.coverCredits(p, journey, ['Place A', 'Place B']).length, 2);   // the cover + the one shared end picture
  assert.equal(R.coverCredits(p, journey, ['Place A', 'Place A']).length, 2);
});

test('a journey id missing from jpic has no cover and no credit, whatever its title', () => {
  const p = world();
  R.register(p, R.coverKey('other'), R.journeyCandidate(['other.webp', 'X'], BASE, null));
  assert.equal(R.coverPhoto(p, journey), null);
  assert.equal(R.coverPhoto(p, { id: 'none', imgwiki: 'Nothing' }), null);
  assert.deepEqual(R.coverCredits(p, { id: 'none' }, [undefined, 'Place Z']), []);
  assert.equal(R.coverPhoto({}, null), null);
});
