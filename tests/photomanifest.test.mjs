// Place photos must be real photos with an author and licence: no logos, maps, flags or emblems.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

test('every stored place photo is a photo with credit and a file on disk', () => {
  const dir = new URL('../photos/places/', import.meta.url);
  const man = JSON.parse(fs.readFileSync(new URL('places.json', dir), 'utf8'));
  const notPhoto = /logo|arrowhead|emblem|coat[_ ]of[_ ]arms|seal[_ ]of|(^|[_ ])flag([_ .]|$)|\.svg/i;
  const bad = [];
  for (const [t, v] of Object.entries(man)) {
    if (notPhoto.test(decodeURIComponent(v.p || ''))) bad.push(t + ': not a photo');
    if (!v.a || !v.l) bad.push(t + ': missing author or licence');
    if (!fs.existsSync(new URL(v.f, dir))) bad.push(t + ': file missing');
  }
  assert.deepEqual(bad, []);
});
