// The journeys {…}[] read from data/journeys/<id>.json (with config.json) when that layout exists (#277), else from the old links.json `cross`.
import fs from 'node:fs';
import path from 'node:path';
export function loadJourneys(root) {
  const dir = path.join(root, 'data', 'journeys');
  if (!fs.existsSync(path.join(dir, 'config.json'))) return JSON.parse(fs.readFileSync(path.join(dir, 'links.json'), 'utf8')).cross || [];
  const rows = fs.readdirSync(dir).filter((f) => f.endsWith('.json') && f !== 'config.json').map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
  return rows.sort((a, b) => (a.pos ?? 0) - (b.pos ?? 0) || (a.id < b.id ? -1 : 1)).map(({ pos, ...rest }) => rest);
}
