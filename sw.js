const V = "79aaf03c";
const SHELL = "atlas-shell-" + V, RT = "atlas-rt";
const SHELL_FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];
const RT_HOSTS = ["tiles.openfreemap.org", "server.arcgisonline.com", "s3.amazonaws.com", "upload.wikimedia.org", "en.wikipedia.org"];
const RT_MAX = 1500;
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("atlas-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
async function trim(c) { const ks = await c.keys(); if (ks.length > RT_MAX) for (const k of ks.slice(0, ks.length - RT_MAX)) await c.delete(k); }
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    // app shell: network first so updates arrive, cache as fallback for offline
    e.respondWith(fetch(r).then(res => { if (res.ok) { const cp = res.clone(); caches.open(SHELL).then(c => c.put(r, cp)); } return res; }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match("./index.html"))));
    return;
  }
  if (RT_HOSTS.includes(u.hostname)) {
    // map tiles, fonts, photos: cache first, fill in from network
    e.respondWith(caches.open(RT).then(c => c.match(r).then(m => m || fetch(r).then(res => { if (res.ok || res.type === "opaque") { c.put(r, res.clone()); trim(c); } return res; }))));
  }
});
