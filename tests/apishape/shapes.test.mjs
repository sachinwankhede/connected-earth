import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

// #725: the app's own suggestion code run on the REAL suggestion files the build wrote (api/search/s-*.json), no browser.
// build/validate_api.py guards the shapes the build writes; this guards that the app still reads them under the same names.
// Needs a built api/ folder (python3 build/build.py --all); the test says so when it is missing.
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const src = (f) => fs.readFileSync(path.join(root, 'src', 'app', f), 'utf8');
function fn(text, name) {   // the source of one top-level-ish function, found by braces, so the test runs the app's code and not a copy
  const i = text.indexOf('function ' + name + '('); assert.ok(i >= 0, name + ' not found in the app source');
  let d = 0, j = text.indexOf('{', i);
  for (let k = j; k < text.length; k++) { if (text[k] === '{') d++; else if (text[k] === '}' && --d === 0) return text.slice(i, k + 1); }
  assert.fail(name + ' has no closing brace');
}
const ctx = {}; vm.createContext(ctx);
vm.runInContext(fn(src('data.js'), 'srchWords') + '\n' + fn(src('suggest.js'), 'sugPick'), ctx);
const dir = path.join(process.env.API_DIR || path.join(root, 'api'), 'search');
test('the suggestion files exist (build first: python3 build/build.py --all)', () => assert.ok(fs.existsSync(dir), 'api/search is missing'));
const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => /^s-[a-z0-9]{2}\.json$/.test(f)).sort() : [];

test('sugPick turns real suggestion files into rows with the fields the dropdown reads', () => {
  let places = 0, species = 0, empty = 0;
  for (const f of files) {
    const d = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const typed = f.slice(2, 4);   // the two letters the file is named for: every row in it has a word starting with them
    const rows = ctx.sugPick(typed, d, 1000);
    for (const r of rows) {
      if (r.t === 'p') { places++; assert.equal(typeof r.id, 'string', f + ': place id'); assert.equal(typeof r.name, 'string', f + ': place name'); }
      else { species++; assert.equal(r.t, 's', f + ': row type'); assert.equal(typeof r.latin, 'string', f + ': species latin'); assert.equal(typeof r.name, 'string', f + ': species name'); assert.equal(typeof r.n, 'number', f + ': species place count'); }
      assert.ok([0, 1, 2].includes(r.k), f + ': rank');
    }
    if (!rows.length && (d.p.length || d.s.length)) empty++;   // a bucket can also hold a word of the short name or an alias the row does not repeat, so a few are fine
  }
  assert.ok(empty <= files.length * 0.05, empty + ' of ' + files.length + ' suggestion files gave no row for their own two letters: the app no longer reads their rows the way the build writes them');
  assert.ok(places > 100 && species > 100, 'expected many place and species rows, got ' + places + ' and ' + species);
});
