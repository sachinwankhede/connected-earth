// Species descriptions come from Wikipedia: pages that are not about the species (disambiguation, towns, names) must never be shown.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { loadSpecies } from '../speciestable.mjs';

test('no species description is a disambiguation page or about something else', () => {
  const tab = loadSpecies(new URL('../..', import.meta.url).pathname);
  const rows = Array.isArray(tab) ? tab : Object.values(tab);
  const bad = /may refer to|can refer to|could refer to|share the common name|is a common name that|:\s*$|\b(given name|female name|male name|surname|unincorporated community|census-designated)\b/i;
  const hits = rows.filter((r) => r && r.about && bad.test(r.about)).map((r) => r.about.slice(0, 60));
  assert.deepEqual(hits, []);
  assert.ok(rows.filter((r) => r && r.about).length > 500, 'descriptions are present');
});
