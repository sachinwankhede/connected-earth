import { createRequire } from 'node:module';
import { test } from 'node:test';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const Registry = require('../src/photo-registry.js');

const legacyPlace = {
  f: 'park.jpg',
  a: 'Photo author',
  l: 'CC BY 4.0',
  lu: 'https://creativecommons.org/licenses/by/4.0/',
  p: 'https://commons.wikimedia.org/wiki/File:Park.jpg',
  mt: 'image/jpeg',
  width: 900,
  height: 600,
  sha256: 'abc'
};

test('adapts legacy place and species records to the shared candidate shape', () => {
  const place = Registry.placeCandidate(legacyPlace, 'photos/places/');
  const species = Registry.speciesCandidate(['2/2f/File.jpg/330px-File.jpg', 'Species_name']);
  assert.equal(place.provider, 'wikimedia-commons');
  assert.equal(place.assetUrl, 'photos/places/park.jpg');
  assert.equal(place.licenseId, 'CC BY 4.0');
  assert.equal(place.mirrorHash, 'abc');
  assert.equal(place.mediaType, 'image/jpeg');
  assert.deepEqual([place.width, place.height], [900, 600]);
  assert.equal(species.assetUrl, 'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2f/File.jpg/120px-File.jpg');
  assert.equal(species.sourcePageUrl, 'https://en.wikipedia.org/wiki/Species_name');
  assert.equal(species.reviewStatus, 'legacy');
});

test('keeps already-absolute Wikimedia assets unchanged and rejects unsafe candidates', () => {
  const direct = 'https://upload.wikimedia.org/wikipedia/commons/a/a0/Exact_file.jpg';
  assert.equal(Registry.speciesCandidate([direct, 'Species']).assetUrl, direct);
  assert.equal(Registry.speciesCandidate(['http://upload.wikimedia.org/a.jpg', 'Species']), null);
  assert.equal(Registry.speciesCandidate(['https://example.com/a.jpg', 'Species']), null);
  assert.equal(Registry.speciesCandidate(['../private/a.jpg', 'Species']), null);
});

test('requires complete secure metadata before a candidate can be approved', () => {
  const approved = {
    provider: 'wikimedia-commons',
    assetUrl: 'https://upload.wikimedia.org/a.jpg',
    sourcePageUrl: 'https://commons.wikimedia.org/wiki/File:A.jpg',
    author: 'A. Photographer',
    licenseId: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    reviewStatus: 'approved',
    mediaType: 'image/jpeg',
    width: 1200,
    height: 800
  };
  assert.deepEqual(Registry.validateCandidate(approved), []);
  assert.ok(Registry.validateCandidate({ ...approved, author: '', licenseId: '' }).includes('author is required'));
  assert.ok(Registry.validateCandidate({ ...approved, licenseUrl: 'http://creativecommons.org/licenses/by/4.0/' }).includes('license URL must use HTTPS'));
  assert.ok(Registry.validateCandidate({ ...approved, mediaType: 'text/html' }).includes('media type must be a supported image MIME type'));
  assert.ok(Registry.validateCandidate({ ...approved, width: 0 }).includes('positive image dimensions are required'));
});

test('preserves local-first ordering and advances to the next approved or legacy candidate', () => {
  const registry = {};
  const species = Registry.speciesCandidate(['a/b/File.jpg/330px-File.jpg', 'Species'], 'Species', 1);
  Registry.register(registry, 'Species', species);
  const place = Registry.placeCandidate(legacyPlace, 'photos/places/');
  Registry.register(registry, 'Species', place);
  Registry.register(registry, 'Species', { ...species, assetUrl: 'https://upload.wikimedia.org/next.jpg', reviewStatus: 'pending-review', priority: 2 });
  assert.deepEqual(registry.Species.candidates.map((c) => c.assetUrl), [
    'photos/places/park.jpg',
    'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/b/File.jpg/120px-File.jpg'
  ]);
  assert.deepEqual(Registry.nextCandidate(registry.Species.candidates, 0, { 'photos/places/park.jpg': true }), {
    index: 1,
    url: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/b/File.jpg/120px-File.jpg'
  });
  assert.equal(Registry.nextCandidate(registry.Species.candidates, 1, {}), null);
});
