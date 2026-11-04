// #241 step 3: every data file the app reads goes through the Data module. This fails if a stray fetch( appears in the app outside Data and the head loader, so a new read cannot skip the one place that knows the addresses.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

// the app is src/app.html plus the pieces it includes (#257); join them the way build/build.py does, so the line patterns below see the whole script
const srcDir = new URL('../../src/', import.meta.url);
const src = fs.readFileSync(new URL('app.html', srcDir), 'utf8').replace(/^__INCLUDE:([\w./-]+)__\n/gm, (_, f) => fs.readFileSync(new URL(f, srcDir), 'utf8'));

test('fetch( is used only by the head loader and the Data module', () => {
  const lines = src.split('\n');
  const dataStart = lines.findIndex((l) => /^  var Data = \(function \(\) \{/.test(l));
  assert.ok(dataStart > 0, 'the Data module is in the app');
  let dataEnd = dataStart;
  while (!/^  \}\)\(\);/.test(lines[dataEnd])) dataEnd++;
  const strays = [];
  lines.forEach((l, i) => {
    if (!/\bfetch\(/.test(l)) return;
    if (i >= dataStart && i <= dataEnd) return;
    if (/window\.__JOURNEYS = .*fetch\(jb \+/.test(l)) return;   // the head loader for the journeys file (#377)
    if (/var get = function \(n\) \{ return fetch\(b \+ n/.test(l)) return;   // the head loader for the world places
    strays.push((i + 1) + ': ' + l.trim().slice(0, 100));
  });
  assert.deepEqual(strays, [], 'read data through Data, not fetch(');
});
