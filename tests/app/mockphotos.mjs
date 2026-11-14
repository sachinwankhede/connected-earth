// Test helper: answers Wikipedia photo requests with generated pictures so photo features can be checked offline.
import fs from 'node:fs';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { readPlaces, FDATA } from './helper.mjs';
import { loadJourneys } from '../journeytable.mjs';
// The pictures' source data. Real data (the default) is read the first time a test asks for it, so a file that uses the fixture build never touches it.
const sources = {};
function source(fixture) {
  const k = fixture ? 'fixture' : 'real';
  if (sources[k]) return sources[k];
  const root = fixture ? FDATA : new URL('../..', import.meta.url).pathname.replace(/\/$/, '');
  const places = readPlaces(true, root), journeyLinks = loadJourneys(root);
  const speciesManifest = JSON.parse(fs.readFileSync(root + '/photos/species.json', 'utf8'));
  let placeManifest = JSON.parse(fs.readFileSync(root + '/photos/places/places.json', 'utf8'));
  // the fixture holds only a few place pictures; every fixture place with a picture title gets an entry shaped like them, so which places lose theirs under thinPlaces (by the title's hash) does not depend on how many pictures the fixture kept
  if (fixture) { const tpl = Object.values(placeManifest)[0]; placeManifest = Object.fromEntries(places.filter((e) => e.imgwiki).map((e) => [e.imgwiki, placeManifest[e.imgwiki] || tpl])); }
  const speciesTitles = new Set([...places.flatMap((e) => e.nodes.map((n) => n.wiki).filter(Boolean)), ...journeyLinks.map((c) => c.imgwiki).filter(Boolean)]);
  return (sources[k] = { places, speciesManifest, placeManifest, speciesTitles });
}
function crc(buf) { let c, crcT = []; for (let n = 0; n < 256; n++) { c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; } let x = 0xffffffff; for (const b of buf) x = crcT[(x ^ b) & 0xff] ^ (x >>> 8); return (x ^ 0xffffffff) >>> 0; }
function chunk(t, d) { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); }
export function png(seed, w = 48, h = 48) {
  let hsh = 0; for (const ch of String(seed)) hsh = (hsh * 31 + ch.charCodeAt(0)) >>> 0;
  const r = 60 + (hsh & 127), g = 60 + ((hsh >> 7) & 127), b = 60 + ((hsh >> 14) & 127), raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3, k = 0.6 + 0.4 * (y / h); raw[o] = r * k; raw[o + 1] = g * k; raw[o + 2] = b * k; } }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
const hostedName = (title) => crypto.createHash('sha1').update(title).digest('hex').slice(0, 12) + '.webp';   // the same shape as a real hosted file name
// For a test that needs only a few hosted species pictures: answers the picture list with exactly `ph` ({title: [file, page]}) and every hosted species file with a generated picture.
export async function mockSpeciesPictures(page, ph = {}) {
  await page.route(/\/api\/species-pictures\.json(?:\?|$)/, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ph, phm: {} }) }));
  await page.route(/\/photos\/species(?:-md)?\/[0-9a-f]{12}\.webp/, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: png(r.request().url()) }));
}
export async function mockPhotos(page, { allPlaces = false, thinPlaces = false, fixture = false } = {}) {   // fixture: take the pictures' source data from the fixture dataset, not the real data (#787)
  const { places: allReal, speciesManifest, placeManifest, speciesTitles } = source(fixture);   // thinPlaces: drop the picture of every place whose title hashes odd, so a test that needs both a picture and an icon does not depend on how many real places have one   // allPlaces: also a picture for each place that names one but has none in the real list (the licence rule, #421, removed some)
  const species = Object.fromEntries([...new Set([...Object.keys(speciesManifest), ...speciesTitles])].map((title) => [title, [hostedName(title), speciesManifest[title]?.[1] || encodeURIComponent(title.replace(/ /g, '_'))]]));
  const places = Object.fromEntries(Object.entries(placeManifest).filter(([title]) => !thinPlaces || crypto.createHash('sha1').update(title).digest()[0] % 2 === 0).map(([title, photo]) => [title, { ...photo, f: `mock/${encodeURIComponent(title)}.png` }]));
  const tpl = Object.values(placeManifest)[0];
  if (allPlaces) for (const e of allReal) if (e.imgwiki && !places[e.imgwiki]) places[e.imgwiki] = { ...tpl, f: `mock/${encodeURIComponent(e.imgwiki)}.png` };
  await page.route(/\/photos\/places\/places\.json(?:\?|$)/, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(places) }));
  await page.route(/\/api\/species-pictures\.json(?:\?|$)/, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ph: species, phm: {} }) }));
  // a place carries its own species picture entries now: give each place file the mocked entries for its species
  await page.route(/\/api\/[\w-]+\.json(?:\?|$)/, async (r) => {
    if (/(species-pictures)\.json/.test(r.request().url())) return r.fallback();
    const res = await r.fetch();
    if (!res.ok()) return r.fallback();   // not a built file: a fixture place is answered by its own route
    const w = await res.json();
    w.ph = {}; w.phm = {};
    for (const n of w.nodes || []) for (const k of [n.wiki, n.canonicalWiki, n.latin]) if (k && species[k]) w.ph[k] = species[k];
    return r.fulfill({ response: res, body: JSON.stringify(w) });
  });
  await page.route(/\/photos\/places\/mock\/|\/photos\/species(?:-md)?\/[0-9a-f]{12}\.webp/, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: png(r.request().url()) }));
  await page.reload();
}
