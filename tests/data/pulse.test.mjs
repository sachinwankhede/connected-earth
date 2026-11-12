import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

// The attention pulse's chunk (#689): which place it ripples from. No browser: the chunk is run in a bare context and only `pick` is called.
const file = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'src', 'chunks', 'pulse.js');
const ctx = { window: {} }; vm.createContext(ctx); vm.runInContext(fs.readFileSync(file, 'utf8'), ctx);
const pick = ctx.window.__chunk.pulse({}).pick;
const box = { cx: 0, cy: 0, w: 100, h: 50 };
const place = (id, lon, lat, nr) => ({ id, lon, lat, idx: { nr } });

test('picks the place with the most links inside the middle of the view', () => {
  const r = pick([place('a', 0, 0, 10), place('b', 10, 5, 30), place('c', 40, 0, 99)], box);   // c is outside the middle half (x = 0.4)
  assert.equal(r.id, 'b');
});
test('nothing near the middle gives no pulse', () => assert.equal(pick([place('c', 40, 0, 99), place('d', 0, 20, 99)], box), null));
test('a place without its link count or position is skipped', () => {
  assert.equal(pick([{ id: 'x', lon: 0, lat: 0 }, { id: 'y', idx: { nr: 5 } }], box), null);
});
