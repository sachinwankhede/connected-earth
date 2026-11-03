// The app's file name for a species (items #253) must be the build's: cut out of the built page, so what runs here is what ships.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const R = new URL('../../', import.meta.url).pathname;
const built = fs.existsSync(R + 'index.html') && fs.existsSync(R + 'api/species-places');

test('every species is in the file the app asks for', { skip: !built && 'build has not run' }, () => {
  const html = fs.readFileSync(R + 'index.html', 'utf8');
  const code = html.match(/  function sppBucket\(l\) \{[^\n]*\}/)[0];
  const ctx = vm.createContext({});
  vm.runInContext(code + ';this.sppBucket = sppBucket;', ctx);
  let n = 0;
  for (const folder of ['species-places', 'species-places-pilot']) {
    for (const f of fs.readdirSync(R + 'api/' + folder)) {
      const d = JSON.parse(fs.readFileSync(R + 'api/' + folder + '/' + f, 'utf8'));
      for (const latin of Object.keys(d)) { assert.equal(ctx.sppBucket(latin) + '.json', f, latin + ' is in ' + f); n++; }
    }
  }
  assert.ok(n > 1500, 'species checked: ' + n);
});
