// Shared helpers for the browser tests. Tests run against the built files:
//   index.html (main app) and pilot/index.html (main + auto-generated places).
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const MAIN = path.join(ROOT, 'index.html');
export const PILOT = path.join(ROOT, 'pilot', 'index.html');
export const SIZES = { phone: { width: 390, height: 750 }, desktop: { width: 1280, height: 800 } };

export function readPlaces(pilot) {
  const dir = (d) => fs.readdirSync(path.join(ROOT, d)).filter((f) => f.endsWith('.json') && f !== 'links.json' && f !== 'order.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(ROOT, d, f), 'utf8')));
  return pilot ? [...dir('data'), ...dir('data-auto')] : dir('data');
}

export async function launch() {
  const exe = process.env.CHROMIUM_PATH || undefined;
  return chromium.launch({
    executablePath: exe,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox'],
  });
}

// Open a page on a build. Map tiles, photos and fonts are blocked so tests are fast and offline.
export async function open(browser, file, size, { hash = '', geo = null, extraCss = '' } = {}) {
  const ctx = await browser.newContext({
    viewport: size,
    ...(geo ? { geolocation: geo, permissions: ['geolocation'] } : {}),
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.route(/openfreemap|arcgis|amazonaws|wikipedia|wikimedia|fonts|cdnjs/, (r) => r.abort());
  await page.goto('file://' + file + hash);
  if (hash) await page.reload();
  await page.waitForFunction(() => window.__M && window.__M.map && window.__M.styleReady, null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(1500);
  if (extraCss) await page.addStyleTag({ content: extraCss });
  return { ctx, page, errors, close: () => ctx.close() };
}

export const dots = (page) => page.evaluate(() => {
  const s = window.__M.map.getSource('atl-e');
  return ((s._data && s._data.features) || []).length;
});
export const camera = (page) => page.evaluate(() => {
  const m = window.__M.map, c = m.getCenter();
  return { lng: +c.lng.toFixed(2), lat: +c.lat.toFixed(2), zoom: +m.getZoom().toFixed(2) };
});
export const jump = async (page, center, zoom) => {
  await page.evaluate(([c, z]) => window.__M.map.jumpTo({ center: c, zoom: z }), [center, zoom]);
  await page.waitForTimeout(900);
};
export const chipLabels = (page) => page.evaluate(() => [...document.querySelectorAll('#kinds .chip')].map((x) => x.textContent.trim()));
export const dimmed = (page) => page.evaluate(() => [...document.querySelectorAll('#kinds .chip.dim')].map((x) => x.getAttribute('data-kind')).sort());
export const hookText = (page) => page.evaluate(() => { const h = document.getElementById('hook'); return h && !h.hidden ? h.textContent : null; });

// The five habitat chips and the data kinds each one stands for
export const GROUPS = {
  'Forest': ['Forest'],
  'Grass & desert': ['Grassland', 'Desert'],
  'Freshwater': ['Lakes & wetlands'],
  'Ocean': ['Coast & ocean'],
  'Cold & high': ['Polar & mountain'],
};

// What the home line should say for a set of places
export function expectedHook(places) {
  const sp = new Set(); let links = 0;
  for (const e of places) {
    for (const n of e.nodes) if (!n.cat && n.latin) sp.add(n.latin.toLowerCase());
    for (const r of e.raw) if (r.length === 2 || r[2] === 's') links++;
  }
  const f = (x) => x.toLocaleString('en-US');
  return `${f(places.length)} places. ${f(sp.size)} species. ${f(links)} links.`;
}
