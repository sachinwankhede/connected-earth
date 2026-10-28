// Test helper: answers Wikipedia photo requests with generated pictures so photo features can be checked offline.
import zlib from 'node:zlib';
function crc(buf) { let c, crcT = []; for (let n = 0; n < 256; n++) { c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; } let x = 0xffffffff; for (const b of buf) x = crcT[(x ^ b) & 0xff] ^ (x >>> 8); return (x ^ 0xffffffff) >>> 0; }
function chunk(t, d) { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); }
export function png(seed, w = 48, h = 48) {
  let hsh = 0; for (const ch of String(seed)) hsh = (hsh * 31 + ch.charCodeAt(0)) >>> 0;
  const r = 60 + (hsh & 127), g = 60 + ((hsh >> 7) & 127), b = 60 + ((hsh >> 14) & 127), raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3, k = 0.6 + 0.4 * (y / h); raw[o] = r * k; raw[o + 1] = g * k; raw[o + 2] = b * k; } }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
export async function mockPhotos(page) {
  await page.route(/en\.wikipedia\.org\/api\/rest_v1\/page\/summary\//, (r) => {
    const t = decodeURIComponent(r.request().url().split('/summary/')[1]);
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ thumbnail: { source: 'https://upload.wikimedia.org/mock/' + encodeURIComponent(t) + '.png' }, content_urls: { desktop: { page: 'https://en.wikipedia.org/wiki/' + t } } }) });
  });
  await page.route(/upload\.wikimedia\.org\/mock\//, (r) => r.fulfill({ status: 200, contentType: 'image/png', body: png(r.request().url()) }));
}
