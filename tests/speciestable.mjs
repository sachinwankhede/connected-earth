// The species table {lowercase Latin name: row}, read from data/species/rows/ when it exists (#276), else from the one old file.
import fs from 'node:fs';
import path from 'node:path';
export function loadSpecies(root) {
  const rows = path.join(root, 'data', 'species', 'rows');
  if (!fs.existsSync(rows)) return JSON.parse(fs.readFileSync(path.join(root, 'data', 'species', 'species.json'), 'utf8'));
  const out = {};
  for (const d of fs.readdirSync(rows)) for (const f of fs.readdirSync(path.join(rows, d))) {
    if (!f.endsWith('.json')) continue;
    const r = JSON.parse(fs.readFileSync(path.join(rows, d, f), 'utf8'));
    out[(r.latin || r.name).toLowerCase()] = r;
  }
  return out;
}
