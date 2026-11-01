// serve.mjs: a small static server that behaves like GitHub Pages for the things that matter to speed: gzip for text files, an ETag, max-age=600,
// and 304 for a conditional request. Used by the perf-ab workflow so a branch and main are served the same way.
//   node tests/perf/serve.mjs <directory> <port>
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const root = path.resolve(process.argv[2] || '.');
const port = +(process.argv[3] || 8080);
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.json': 'application/json',
  '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.webmanifest': 'application/manifest+json', '.txt': 'text/plain; charset=utf-8',
};
const GZIP = new Set(['.html', '.js', '.mjs', '.json', '.css', '.svg', '.webmanifest', '.txt']);
const cache = new Map();   // path -> { buf, gz, etag }, so compression time is not part of what is measured

function load(file) {
  const st = fs.statSync(file);
  const hit = cache.get(file);
  if (hit && hit.mtime === st.mtimeMs) return hit;
  const buf = fs.readFileSync(file);
  const ext = path.extname(file).toLowerCase();
  const entry = { mtime: st.mtimeMs, buf, gz: GZIP.has(ext) ? zlib.gzipSync(buf, { level: 6 }) : null, etag: '"' + buf.length.toString(16) + '-' + Math.round(st.mtimeMs).toString(16) + '"', ext };
  cache.set(file, entry);
  return entry;
}

http.createServer((req, res) => {
  let p;
  try { p = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch (e) { res.writeHead(400); return res.end(); }
  if (p.endsWith('/')) p += 'index.html';
  const file = path.join(root, p);
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404, { 'content-type': 'text/plain' }); return res.end('not found'); }
  const e = load(file);
  const h = { 'content-type': TYPES[e.ext] || 'application/octet-stream', etag: e.etag, 'cache-control': 'max-age=600', vary: 'Accept-Encoding' };
  if (req.headers['if-none-match'] === e.etag) { res.writeHead(304, h); return res.end(); }
  if (e.gz && /\bgzip\b/.test(req.headers['accept-encoding'] || '')) { h['content-encoding'] = 'gzip'; h['content-length'] = e.gz.length; res.writeHead(200, h); return res.end(e.gz); }
  h['content-length'] = e.buf.length;
  res.writeHead(200, h);
  res.end(e.buf);
}).listen(port, '127.0.0.1', () => console.log('serving', root, 'on http://localhost:' + port + '/'));
