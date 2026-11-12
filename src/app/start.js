  M.h0 = location.hash.slice(1);
  buildMap();
  if (window.maplibregl || window.__mapLib) initMap(); else window.__mapReady = initMap;   /* the map library follows this script in the page: the places list draws first, the map starts the moment the library has arrived */
  M.fromHash = true;   /* start-up first draws the map and then applies the address: neither is a new history step, and the first draw must not wipe the entry's state (#412) */
  showMap();
  applyHash(M.h0);
  addEventListener("hashchange", function () { applyHash(); });
  var PB = location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "") + "photos/places/";
  var man = null, manAsked = false;   /* the stored place photo list: fetched when the photos are released (#397), not at start; nothing reads it before it has arrived */
  function stored(t) {
    var m = man && man[t], candidate = m && PhotoRegistry.placeCandidate(m, PB);
    if (candidate) PhotoRegistry.register(PHOTOS, t, candidate);
  }
  /* Place photos are loaded only from the approved local manifest. */
  /* pictures wait for the map (or a touch, or 9 s): they competed with its tiles */
  M.photoGo = false; var HELD = [];
  M.loadD3 = loadD3;   /* the tests start the library download by hand */
  M.releasePhotos = function () {
    if (M.photoGo) return;
    M.photoGo = true;
    if (!manAsked) { manAsked = true; Data.placePhotos().then(function (m) { man = m || {}; var h = HELD; HELD = []; h.forEach(function (f) { f(); }); }); }   /* a failed fetch gives {} (Data.placePhotos) */
    setTimeout(loadD3, 4500);   /* the diagram library follows the map, so the first food web opens at once */
    setTimeout(ensureStates, 4000);   /* the US state outlines follow the map too */
    if (M.heldLoad) { M.heldLoad = false; loadPhotos(); }
  };
  var wp = M.wantPhoto = function (e) {
    if (!e.imgwiki) return;
    if (!man) { if (!e.held) { e.held = 1; HELD.push(function () { e.held = 0; wp(e); }); } return; }
    var tt = e.imgwiki; stored(tt);
    if (PHOTOS[tt]) { ecoPhoto(e); return; }
  };
  M.placePhotos = function (titles, done) {   /* the dropdown rows of places that have no card yet: release the photos, then read their entries from the stored list */
    M.releasePhotos(); var go = function () { titles.forEach(stored); done(); }; if (man) go(); else HELD.push(go);
  };
  function crossPhotos() {
    CROSS.forEach(function (c) {
      var tt = c.imgwiki;
      if (!tt) return; stored(tt);
      if (PHOTOS[tt]) { linkPhoto(c); return; }
    });
  }
  ECOS.forEach(function (e) { if (e.li) M.wantPhoto(e); });
  if (window.fetch) HELD.push(crossPhotos);
  var goPhotos = function () { M.releasePhotos(); };
  addEventListener("pointerdown", loadCounts, { once: true, capture: true });   /* the per-region counts are fetched at the first touch, not at start: the first view makes no request for them (#261) */
  addEventListener("pointerdown", goPhotos, { once: true, capture: true }); addEventListener("keydown", goPhotos, { once: true, capture: true });
  setTimeout(goPhotos, 9000);
  if (/[#&](pg|p|e|j)=/.test(location.hash)) goPhotos();   // a link straight to a place or journey needs its picture now
  else {
    var hookIdle = function () { if (M.styleReady && M.map.loaded()) { goPhotos(); return; } M.map.on("idle", function f() { if (M.styleReady && M.map.loaded()) { M.map.off("idle", f); goPhotos(); } }); };
    if (M.map) hookIdle(); else M.mapHooks = (M.mapHooks || []).concat(hookIdle);   // the map library can arrive after this point: hook the map when it is created
  /* the attention pulse (#689): one quiet ripple, once, from a lazy chunk, a moment after the map settles; never with reduced motion, a link to a place, or after a first touch */
  if (!M.stub && !/[#&](pg|p|e|j)=/.test(location.hash) && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    addEventListener("pointerdown", function () { M.pt = 1; }, { once: true, capture: true }); addEventListener("keydown", function () { M.pt = 1; }, { once: true, capture: true });
    var hookPulse = function () { var go = function () { setTimeout(function () { if (M.pt) return; var sc = document.createElement("script"); sc.async = true; sc.src = chunkURL("pulse-__PULSEVER__"); sc.onload = function () { var f = (window.__chunk || {}).pulse; if (f) f({ map: M.map, eco: function () { return ECOS; }, touched: function () { return M.pt; } })(); }; document.head.appendChild(sc); }, 1200); }; if (M.styleReady && M.map.loaded()) go(); else M.map.once("idle", go); };
    if (M.map) hookPulse(); else M.mapHooks = (M.mapHooks || []).concat(hookPulse);
  }
  }
