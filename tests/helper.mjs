// Shared helpers for the browser tests. Tests run against the built files:
//   index.html (main app) and pilot/index.html (main + auto-generated places).
import { chromium } from 'playwright';
import { after } from 'node:test';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const MAIN = path.join(ROOT, 'index.html');
export const PILOT = path.join(ROOT, 'pilot', 'index.html');
// The app fetches its place files with fetch(). Newer Chromium builds (as on CI) refuse fetch() on file:// pages,
// so tests load the built files from a small local web server instead, as the real site does.
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webmanifest': 'application/manifest+json', '.css': 'text/css', '.svg': 'image/svg+xml' };
let serverP = null;
let serverOffline = false;
function server() {
  if (!serverP) serverP = new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      if (serverOffline) { req.socket.destroy(); return; }
      const rel = decodeURIComponent((req.url || '/').split('?')[0].split('#')[0]);
      const f = path.join(ROOT, rel === '/' ? 'index.html' : rel);
      if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.statusCode = 404; res.end(); return; }
      res.setHeader('content-type', MIME[path.extname(f)] || 'application/octet-stream'); res.end(fs.readFileSync(f));
    });
    srv.unref(); srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
  return serverP;
}
export async function urlFor(file) { const srv = await server(); return `http://127.0.0.1:${srv.address().port}/` + path.relative(ROOT, file).split(path.sep).join('/'); }
export function setServerOffline(offline) { serverOffline = offline; }

export const SIZES = { phone: { width: 390, height: 750 }, desktop: { width: 1280, height: 800 } };

// Places drawn on the map at the world view with the Local parks button off: auto-generated national places appear only once zoomed in.
export const atWorld = (places) => places.filter((e) => !e.auto && e.level !== 'local');
const TABLE = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'species.json'), 'utf8'));
// Same join as build/species.py: a place keeps only what differs from the shared species row.
const join = (e) => ({ ...e, nodes: e.nodes.map((n) => {
  const { sp, no, ...rest } = n, base = TABLE[sp] || {}, full = { ...base, ...rest };
  for (const f of no || []) delete full[f];
  if (base.wiki && full.wiki && full.wiki !== base.wiki) full.canonicalWiki = base.wiki;
  return full;
}) });
export function readPlaces(pilot) {
  const dir = (d) => fs.readdirSync(path.join(ROOT, d)).filter((f) => f.endsWith('.json') && !['links.json', 'order.json', 'species.json', 'bounds.json'].includes(f))
    .map((f) => join(JSON.parse(fs.readFileSync(path.join(ROOT, d, f), 'utf8'))));
  return pilot ? [...dir('data'), ...dir('data-auto')] : dir('data');
}

// One Chromium per test file (each file runs in its own process). Starting a browser is slow with software rendering,
// so tests share it; every test still gets its own fresh context, and b.close() closes that test's contexts only.
let shared = null;
after(async () => { if (shared) { const br = await shared; await br.close().catch(() => {}); } });
export async function launch() {
  if (!shared) {
    const exe = process.env.CHROMIUM_PATH || undefined;
    shared = chromium.launch({
      executablePath: exe,
      args: ['--allow-file-access-from-files', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox'],
    });
  }
  const br = await shared, mine = [];
  return {
    newContext: async (o) => { const c = await br.newContext(o); mine.push(c); return c; },
    close: async () => { await Promise.all(mine.splice(0).map((c) => c.close().catch(() => {}))); },
  };
}

// Open a page on a build. Map tiles, photos and fonts are blocked so tests are fast and offline.
export async function open(browser, file, size, { hash = '', geo = null, extraCss = '' } = {}) {
  const ctx = await browser.newContext({
    viewport: size,
    ...(geo ? { geolocation: geo, permissions: ['geolocation'] } : {}),
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(90000); // CI machines draw the map in software and can be several times slower than a laptop
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
  await page.goto((await urlFor(file)) + hash);
  if (hash) await page.reload();
  await page.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 90000 }).catch(() => {});
  await page.waitForTimeout(500);
  if (extraCss) await page.addStyleTag({ content: extraCss });
  return { ctx, page, errors, close: () => ctx.close() };
}

export const dots = (page) => page.evaluate(() => {
  const n = (id) => { const s = window.__M.map.getSource(id); return ((s._data && s._data.features) || []).length; };
  return n('atl-e') + n('atl-f');
});
export const camera = (page) => page.evaluate(() => {
  const m = window.__M.map, c = m.getCenter();
  return { lng: +c.lng.toFixed(2), lat: +c.lat.toFixed(2), zoom: +m.getZoom().toFixed(2) };
});
export const jump = async (page, center, zoom) => {
  await page.evaluate(([c, z]) => { window.__M.map.jumpTo({ center: c, zoom: z }); }, [center, zoom]);
  await page.waitForTimeout(600);
};
export const chipLabels = (page) => page.evaluate(() => [...document.querySelectorAll('#kinds .chip')].map((x) => x.textContent.trim()));
export const dimmed = (page) => page.evaluate(() => [...document.querySelectorAll('#kinds .chip.dim')].map((x) => x.getAttribute('data-kind')).sort());
export const hookText = (page) => page.evaluate(() => { const h = document.getElementById('hook'); return h && !h.hidden ? h.querySelector('.stat').textContent : null; });

// The five habitat chips and the data kinds each one stands for
export const GROUPS = {
  'Forest': ['Forest'],
  'Grass & desert': ['Grassland', 'Desert'],
  'Freshwater': ['Lakes & wetlands'],
  'Ocean': ['Coast & ocean'],
  'Cold & high': ['Polar & mountain'],
};

// What the home line should say for a set of places
export const HOOK = 'What eats what, and where it travels';
export function expectedHook(places) {
  const sp = new Set(); let links = 0;
  for (const e of places) {
    for (const n of e.nodes) if (!n.cat && n.latin) sp.add(n.latin.toLowerCase());
    for (const r of e.raw) if (r.length === 2 || r[2] === 's') links++;
  }
  const f = (x) => x.toLocaleString('en-US');
  return `${f(places.length)} places \u00b7 ${f(sp.size)} species`;
}
