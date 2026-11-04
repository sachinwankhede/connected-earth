  M.h0 = location.hash.slice(1);
  buildMap();
  if (window.maplibregl || window.__mapLib) initMap(); else window.__mapReady = initMap;   /* the map library follows this script in the page: the places list draws first, the map starts the moment the library has arrived */
  showMap();
  applyHash(M.h0);
  addEventListener("hashchange", function () { applyHash(); });
  var PB = location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "") + "photos/places/";
  Data.placePhotos().then(function (man) {
    function stored(t) {
      var m = man[t], candidate = m && PhotoRegistry.placeCandidate(m, PB);
      if (candidate) PhotoRegistry.register(PHOTOS, t, candidate);
    }
  /* Place photos are loaded only from the approved local manifest. */
  /* pictures wait until the map has drawn (or the person touches the page, or 9 seconds pass): on a slow connection they were competing with the map's own tiles */
  M.photoGo = false; var HELD = [];
  M.loadD3 = loadD3;   /* the tests start the library download by hand */
  M.releasePhotos = function () {
    if (M.photoGo) return;
    M.photoGo = true; var h = HELD; HELD = []; h.forEach(function (f) { f(); });
    setTimeout(loadD3, 4500);   /* the diagram library follows the map, so the first food web opens at once */
    setTimeout(ensureStates, 4000);   /* the US state outlines follow the map too */
    if (M.heldLoad) { M.heldLoad = false; loadPhotos(); }
  };
  var wp = M.wantPhoto = function (e) {
    if (!e.imgwiki) return;
    if (!M.photoGo) { if (!e.held) { e.held = 1; HELD.push(function () { e.held = 0; wp(e); }); } return; }
    var tt = e.imgwiki; stored(tt);
    if (PHOTOS[tt]) { ecoPhoto(e); return; }
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
  var go = function () { M.releasePhotos(); };
  addEventListener("pointerdown", loadCounts, { once: true, capture: true });   /* the per-region counts are fetched at the first touch, not at start: the first view makes no request for them (#261) */
  addEventListener("pointerdown", go, { once: true, capture: true }); addEventListener("keydown", go, { once: true, capture: true });
  setTimeout(go, 9000);
  if (/[#&](pg|p|e|j)=/.test(location.hash)) go();   // a link straight to a place or journey needs its picture now
  else {
    var hookIdle = function () { if (M.styleReady && M.map.loaded()) { go(); return; } M.map.on("idle", function f() { if (M.styleReady && M.map.loaded()) { M.map.off("idle", f); go(); } }); };
    if (M.map) hookIdle(); else M.mapHooks = (M.mapHooks || []).concat(hookIdle);   // the map library can arrive after this point: hook the map when it is created
  }
  });
