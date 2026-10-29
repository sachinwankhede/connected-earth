// "The story" and "Why it matters" must stay short enough for a phone screen (limits live in docs/DESIGN.md).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const MAX = { story: 60, matters: 40 };
const words = (t) => String(t || '').trim().split(/\s+/).filter(Boolean).length;

test('place story and why-it-matters texts stay within the word limits', () => {
  const dirs = ['../data/', '../data-auto/'];
  const over = [];
  let checked = 0;
  for (const d of dirs) {
    for (const f of fs.readdirSync(new URL(d, import.meta.url)).filter((n) => n.endsWith('.json'))) {
      let j;
      try { j = JSON.parse(fs.readFileSync(new URL(d + f, import.meta.url), 'utf8')); } catch { continue; }
      if (!j || typeof j !== 'object' || Array.isArray(j)) continue;
      for (const [k, max] of Object.entries(MAX)) {
        if (!j[k]) continue;
        checked++;
        const n = words(j[k]);
        if (n > max) over.push(`${f} ${k}: ${n} words (max ${max})`);
      }
    }
  }
  assert.ok(checked >= 10, 'texts were found to check');
  assert.deepEqual(over, []);
});

test('place summaries are one short sentence about the place, never a disambiguation page', () => {
  const sums = JSON.parse(fs.readFileSync(new URL('../pipeline/summaries.json', import.meta.url), 'utf8'));
  const bad = /may refer to|can refer to|could refer to|share the common name|is a common name that|:\s*$|\(/;
  const over = Object.entries(sums).filter(([, t]) => t && (words(t) > 40 || bad.test(t))).map(([k, t]) => `${k}: ${t.slice(0, 60)}`);
  assert.deepEqual(over, []);
});
