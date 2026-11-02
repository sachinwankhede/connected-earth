const V = "__BUILD__";
const SHELL = "atlas-shell-" + V, RT = "atlas-rt";
const SHELL_FILES = ["./", "./index.html", "./maplibre-gl-__MLVER__.js", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];
const RT_HOSTS = ["tiles.openfreemap.org", "server.arcgisonline.com", "s3.amazonaws.com", "upload.wikimedia.org", "thumb.wikimedia.org"];
const RT_MAX = 1500;
self.addEventListener("install", e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("atlas-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
async function trim(c) { const ks = await c.keys(); if (ks.length > RT_MAX) for (const k of ks.slice(0, ks.length - RT_MAX)) await c.delete(k); }
async function cacheResponse(c, r, res, limit = false) {
  if (res.ok || res.type === "opaque") {
    try {
      await c.put(r, res.clone());
      if (limit) await trim(c);
    } catch (err) {
      console.warn("Service worker could not update its cache", err);
    }
  }
  return res;
}
async function networkFirst(c, r) {
  try {
    return await cacheResponse(c, r, await fetch(r), true);
  } catch (err) {
    const m = await c.match(r);
    if (m) return m;
    throw err;
  }
}
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    // app shell: network first so updates arrive, cache as fallback for offline
    const navigation = r.mode === "navigate" || r.destination === "document";
    const document = navigation || u.pathname.endsWith("/") || u.pathname.endsWith(".html");
    const q = document ? new Request(r.url, { cache: "no-cache", credentials: "same-origin" }) : r;
    e.respondWith(caches.open(SHELL).then(async c => {
      try {
        const res = await fetch(q);
        return await cacheResponse(c, r, res);
      } catch (err) {
        const cached = await c.match(r, { ignoreSearch: true });
        if (cached) return cached;
        if (navigation) {
          const shell = await c.match("./index.html");
          if (shell) return shell;
        }
        throw err;
      }
    }));
    return;
  }
  if (RT_HOSTS.includes(u.hostname)) {
    // Styles can change independently of the app shell; map tiles, fonts and photos remain cache-first.
    const updateStyle = u.hostname === "tiles.openfreemap.org" && (u.pathname.startsWith("/styles/") || u.pathname === "/planet");
    e.respondWith(caches.open(RT).then(async c => {
      if (updateStyle) return networkFirst(c, r);
      const cached = await c.match(r);
      return cached || cacheResponse(c, r, await fetch(r), true);
    }));
  }
});
