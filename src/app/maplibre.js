  /* ---------- MapLibre GL layer: real basemap (streets, cities), terrain and 3D ---------- */
  var GLYPHS = "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf";
  var STYLES = { streets: "https://tiles.openfreemap.org/styles/liberty", light: "https://tiles.openfreemap.org/styles/positron" };
  var DEM_TILES = ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"];
  M.mode = "satellite"; M.tilt = false; M.needFit = true; M.styleReady = false; M.stub = M.stubUrl = /[#&?]stub/.test(location.href); M.fails = {}; M.retries = 0;
  function cssv(n, d) { var v = getComputedStyle(document.documentElement).getPropertyValue(n).trim(); return v || d; }
  M.countryBy = {}; M.stateBy = {};
  GEO.countries.forEach(function (c) { M.countryBy[c.name] = c; });
  /* make every ring continuous across the antimeridian (and close polar rings) so polygons don't streak across the map */
  function unwrapRing(r) {
    var o = [], off = 0, prev = null;
    r.forEach(function (p) { var x = p[0] + off; if (prev !== null) { if (x - prev > 180) { off -= 360; x -= 360; } else if (x - prev < -180) { off += 360; x += 360; } } o.push([x, p[1]]); prev = x; });
    var d = o[o.length - 1][0] - o[0][0];
    if (Math.abs(d) > 180) { var lat = o[0][1] < 0 ? -85 : 85; o.push([o[o.length - 1][0], lat], [o[0][0], lat], o[0].slice()); }
    return o;
  }
  function unwrapGeom(g) {
    if (g.type === "Polygon") return { type: "Polygon", coordinates: g.coordinates.map(unwrapRing) };
    return { type: "MultiPolygon", coordinates: g.coordinates.map(function (poly) { return poly.map(unwrapRing); }) };
  }
  var GJ_C = { type: "FeatureCollection", features: GEO.countries.map(function (c) { return { type: "Feature", properties: { name: c.name, cont: c.cont }, geometry: unwrapGeom(c.g) }; }) };
  var GJ_S = { type: "FeatureCollection", features: [] };
  /* the US state outlines are their own file (geo-states.json), fetched in the quiet time after the map, or at once when a state is asked for */
  M.statesP = null;
  function ensureStates() {
    if (M.statesP) return M.statesP;
    M.statesP = Data.states().then(function (st) {
      st.forEach(function (x) { M.stateBy[x.name] = x; });
      GJ_S.features = st.map(function (x) { return { type: "Feature", properties: { name: x.name }, geometry: unwrapGeom(x.g) }; });
      var src = M.map && M.styleReady && M.map.getSource("atl-s"); if (src) src.setData(GJ_S);
      if (view.level === "state") renderView(true);
      return true;
    }).catch(function () { M.statesP = null; return false; });
    return M.statesP;
  }
  var EMPTY = { type: "FeatureCollection", features: [] };
  var LK = {}; CROSS.forEach(function (c) { ecoEnds(c).forEach(function (en) { LK[en.eco] = 1; }); });
  var DOT = window.matchMedia && matchMedia("(pointer: coarse)").matches ? 6.5 : 4.5;
  var SAT_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  function satStyle() {
    var lab = { "text-font": ["Noto Sans Bold"] }, pnt = { "text-color": "#ffffff", "text-halo-color": "rgba(0,0,0,0.7)", "text-halo-width": 1.5 }, nm = ["coalesce", ["get", "name:latin"], ["get", "name"]];
    function pl(id, cls, minz, maxz, size, extra) { var l = { id: id, type: "symbol", source: "openmaptiles", "source-layer": "place", filter: ["in", ["get", "class"], ["literal", cls]], minzoom: minz, layout: { "text-field": nm, "text-font": lab["text-font"], "text-size": size }, paint: pnt }; if (maxz) l.maxzoom = maxz; if (extra) for (var k in extra) l.layout[k] = extra[k]; return l; }
    return { version: 8, name: "satellite", glyphs: GLYPHS, sources: {
      sat0: { type: "raster", tiles: [SAT_TILES], tileSize: 512, maxzoom: 1 },   /* the opening world view: the same 256 px pictures counted as 512, so the phone asks for the 2 x 2 world tiles instead of about 12 (#244) */
      sat: { type: "raster", tiles: [SAT_TILES], tileSize: 256, maxzoom: 18, attribution: "Imagery &copy; Esri, Maxar, Earthstar Geographics" },
      openmaptiles: { type: "vector", url: "https://tiles.openfreemap.org/planet" } },
    layers: [
      { id: "sat0", type: "raster", source: "sat0", maxzoom: 1.2 },
      { id: "sat", type: "raster", source: "sat", minzoom: 1, paint: { "raster-opacity": ["interpolate", ["linear"], ["zoom"], 1, 0, 1.2, 1] } },   /* a layer outside its zoom range asks for no tiles: the detailed tiles load only from zoom 1, fading in over the coarse ones */
      { id: "park", type: "fill", source: "openmaptiles", "source-layer": "park", paint: { "fill-color": "#000000", "fill-opacity": 0 } },
      { id: "sat-state-line", type: "line", source: "openmaptiles", "source-layer": "boundary", minzoom: 3, filter: ["all", ["==", ["get", "admin_level"], 4], ["!=", ["get", "maritime"], 1], ["!=", ["get", "disputed"], 1]], layout: { "line-join": "round" }, paint: { "line-color": "#ffffff", "line-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.35, 6, 0.7], "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 8, 1.4], "line-dasharray": [4, 2.5] } },
      pl("sat-country", ["country"], 1, 6, 12, { "text-transform": "uppercase", "text-letter-spacing": 0.12 }),
      pl("sat-state", ["state"], 4, 8, 11, { "text-transform": "uppercase", "text-letter-spacing": 0.08 }),
      pl("sat-city", ["city"], 3, 0, ["interpolate", ["linear"], ["zoom"], 3, 11, 10, 16]),
      pl("sat-town", ["town"], 7, 0, 12),
      pl("sat-village", ["village", "suburb"], 10, 0, 11)] };
  }
  function sheetMode() { return window.matchMedia && matchMedia("(max-width: 700px)").matches; }
  function stubStyle() { return { version: 8, name: "plain", sources: {}, glyphs: GLYPHS, layers: [{ id: "bg", type: "background", paint: { "background-color": cssv("--sea-a", "#cfe6f4") } }] }; }
  function pt(e, extra) { var p = { id: e.id, short: e.short, kc: KC[e.kind] || "#888", lk: LK[e.id] ? 1 : 0 }; for (var k in extra) p[k] = extra[k]; return { type: "Feature", properties: p, geometry: { type: "Point", coordinates: [e.lon, e.lat] } }; }
  var FLAGS = ["yellowstone", "amazon", "serengeti", "congo", "reef", "arctic", "mississippi", "galapagos", "boreal", "baikal", "himalaya", "greatlakes"];
  function flagMode() { return !M.hiZ && view.level === "world" && !(FL.q && FL.q.length >= 2); }
  function flagFC() { var fm = flagMode(); return { type: "FeatureCollection", features: !fm ? [] : ECOS.filter(function (e) { return FLAGS.indexOf(e.id) >= 0 && inRegion(e); }).map(function (e) { return pt(e, { pr: FLAGS.indexOf(e.id) }); }) }; }
  function dotStyle() {
    var m = M.map; if (!m || !m.getLayer("atl-pt")) return;
    var fm = flagMode();
    m.setPaintProperty("atl-pt", "circle-radius", fm ? ["interpolate", ["linear"], ["zoom"], 1, 1.6, 2.4, 2.6, 3.5, DOT] : ["interpolate", ["linear"], ["zoom"], 1, DOT - 1.5, 5, DOT]);
    m.setPaintProperty("atl-f-pt", "circle-radius", ["interpolate", ["linear"], ["zoom"], 0.6, 3.6, 2.4, 5, 3.5, DOT + 2]);
    m.setPaintProperty("atl-f-pt", "circle-stroke-width", ["interpolate", ["linear"], ["zoom"], 0.6, 0.6, 3.5, 1.2]);
    ["atl-lb", "atl-pt", "atl-cl", "atl-cl-n"].forEach(function (l) { if (m.getLayer(l)) m.setLayoutProperty(l, "visibility", fm ? "none" : "visible"); });
    if (m.getLayer("atl-n-pt")) m.setLayoutProperty("atl-n-pt", "visibility", fm ? "visible" : "none");
    m.setPaintProperty("atl-pt", "circle-stroke-width", fm ? ["interpolate", ["linear"], ["zoom"], 1, 0.15, 2.4, 0.3, 3.5, 0.7] : 0.7);
  }
  function setEco() { var m = M.map; dotStyle(); var fc = ecoFC(); if (m.getSource("atl-n")) m.getSource("atl-n").setData(flagMode() ? fc : EMPTY_FC); m.getSource("atl-e").setData(fc); m.getSource("atl-el").setData(fc); var ff = flagFC(); m.getSource("atl-f").setData(ff); m.getSource("atl-fl").setData(ff); }
  function ecoFC() { var fm = flagMode(); return { type: "FeatureCollection", features: ECOS.filter(function (e) { return !(fm && FLAGS.indexOf(e.id) >= 0) && inRegion(e) && (!e.auto || e.level === "local" || M.hiZ || FL.q || view.level !== "world"); }).map(function (e) { return pt(e); }) }; }
  function gbox(g) {
    var b = [Infinity, Infinity, -Infinity, -Infinity];
    (function w(a) { if (typeof a[0] === "number") { b[0] = Math.min(b[0], a[0]); b[1] = Math.min(b[1], a[1]); b[2] = Math.max(b[2], a[0]); b[3] = Math.max(b[3], a[1]); } else a.forEach(w); })(g.coordinates);
    return b;
  }
  function regionBounds() {
    if (view.level === "world") return M.map && M.map.getContainer().clientWidth < 560 ? [[-132, -40], [48, 64]] : [[-168, -56], [180, 74]];
    if (view.level === "continent") { var c = CONT_BOX[view.cont]; return [[c[0], Math.max(c[1], -80)], [c[2], c[3]]]; }
    if (view.level === "country" && COUNTRY_BOX[view.country]) { var q = COUNTRY_BOX[view.country]; return [[q[0], q[1]], [q[2], q[3]]]; }
    var g = view.level === "state" ? M.stateBy[view.state] : M.countryBy[view.country], b = g ? gbox(g.g) : [Infinity, Infinity, -Infinity, -Infinity];
    var geoOk = g && (b[2] - b[0]) <= 100;
    if (!geoOk) b = [Infinity, Infinity, -Infinity, -Infinity];
    ECOS.filter(inRegion).forEach(function (e) {
      if (geoOk && (e.lon < b[0] - 12 || e.lon > b[2] + 12 || e.lat < b[1] - 12 || e.lat > b[3] + 12)) return;
      b = [Math.min(b[0], e.lon), Math.min(b[1], e.lat), Math.max(b[2], e.lon), Math.max(b[3], e.lat)];
    });
    if (!isFinite(b[0])) return [[-168, -56], [180, 74]];
    if (b[2] - b[0] < 4) { var mx = (b[0] + b[2]) / 2; b[0] = mx - 2; b[2] = mx + 2; }
    if (b[3] - b[1] < 3) { var my = (b[1] + b[3]) / 2; b[1] = my - 1.5; b[3] = my + 1.5; }
    return [[b[0], b[1]], [b[2], b[3]]];
  }
  function matchBounds() {
    var b = [Infinity, Infinity, -Infinity, -Infinity], n = 0;
    ECOS.filter(inRegion).forEach(function (e) { n++; b = [Math.min(b[0], e.lon), Math.min(b[1], e.lat), Math.max(b[2], e.lon), Math.max(b[3], e.lat)]; });
    if (!n) return null;
    if (b[2] - b[0] < 4) { var mx = (b[0] + b[2]) / 2; b[0] = mx - 2; b[2] = mx + 2; }
    if (b[3] - b[1] < 3) { var my = (b[1] + b[3]) / 2; b[1] = my - 1.5; b[3] = my + 1.5; }
    return [[b[0], b[1]], [b[2], b[3]]];
  }
  /* "Found in N ecosystems": every web that holds the same species, shown on the map */
  function speciesMap(name, latin) {   /* the places of a species come from its small file (api/species-places); without a Latin name the word index is used */
    var q = name.toLowerCase();
    if (!FL.q) M.pushNext = true;   /* a species filter that starts from no search is a step Back can undo (#412) */
    FL.q = q; FL.hits = latin ? new Set() : null;
    if (latin) sppPlaces(latin).then(function (ids) { if (FL.q === q && FL.hits) { FL.hits = new Set(ids); M.pgKey = null; filterView(); } }); else searchFor(q); if (M.tab === "journeys") setTab("places"); FL.kind = null; FL.park = false; view = { level: "world", cont: null, country: null, state: null }; view.focus = null;
    document.getElementById("q").value = name; qSync();
    document.getElementById("peek").hidden = true; showTies(null);
    showMap(); renderView(true);
    window.scrollTo(0, 0);
  }
  function mapFit(animate) {
    var m = M.map; if (!m) return;
    M.needFit = false; M.prevCam = null;
    var phone = m.getContainer().clientWidth < 560, pad = phone ? (sheetMode() ? { top: 120, bottom: 110, left: 24, right: 24 } : 18) : 40;
    var rb = FL.q && FL.q.length >= 3 && view.level === "world" ? matchBounds() : null;
    m.fitBounds(rb || regionBounds(), { padding: pad, maxZoom: view.level === "state" ? 8 : view.level === "country" ? 7 : 4.2, duration: animate && !reduce ? 900 : 0, bearing: 0, pitch: M.tilt ? 58 : 0 });
  }
  function addOverlay() {
    var m = M.map, first = null;
    try {
      var sn = ECOS.map(function (e) { return e.short; });
      (m.getStyle().layers || []).forEach(function (l) {
        if (l.type === "symbol" && l["source-layer"] === "place" && l.layout && l.layout["text-field"]) {
          var f0 = l.filter || ["all"];
          m.setFilter(l.id, ["all", f0, ["!", ["in", ["coalesce", ["get", "name:latin"], ["get", "name"]], ["literal", sn]]]]);
        }
      });
    } catch (x) {}
    (m.getStyle().layers || []).some(function (l) { if (l.type === "symbol") { first = l.id; return true; } return false; });
    var ink = cssv("--ink", "#1d2a24"), surf = cssv("--surface", "#ffffff"), acc = cssv("--accent", "#0e7a6b"), land = cssv("--land", "#eef1e6");
    ["atl-c", "atl-s"].forEach(function (id) { m.addSource(id, { type: "geojson", data: id === "atl-c" ? GJ_C : GJ_S }); });
    /* dots and their text use two sources, so a failed font download can never hide the dots */
    m.addSource("atl-bound", { type: "geojson", data: M.boundFC || EMPTY_FC });
    m.addSource("atl-e", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });
    m.addSource("atl-f", { type: "geojson", data: EMPTY_FC });
    m.addSource("atl-n", { type: "geojson", data: EMPTY_FC });
    m.addSource("atl-fl", { type: "geojson", data: EMPTY_FC });
    m.addSource("atl-el", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });
    var dimT = null; m.on("moveend", function () { clearTimeout(dimT); dimT = setTimeout(dimChips, 330); });
    m.on("zoomend", function () { var hi = m.getZoom() >= 3.5; if (hi !== !!M.hiZ) { M.hiZ = hi; if (!m.getSource("atl-e")) return; setEco(); } });
    ["atl-t", "atl-tie", "atl-arc", "atl-al"].forEach(function (id) { m.addSource(id, { type: "geojson", data: EMPTY }); });
    m.addSource("atl-src", { type: "geojson", data: { type: "FeatureCollection", features: Object.keys(SRC).map(function (k) { return { type: "Feature", properties: { name: SRC[k].name }, geometry: { type: "Point", coordinates: [SRC[k].lon, SRC[k].lat] } }; }) } });
    if (M.tilt) {
      m.addSource("atl-dem", { type: "raster-dem", tiles: DEM_TILES, encoding: "terrarium", tileSize: 256, maxzoom: 14, attribution: "Terrain: Mapzen, AWS Open Data" });
    }
    if (M.stub) {
      m.addLayer({ id: "atl-base", type: "fill", source: "atl-c", paint: { "fill-color": land } }, first || undefined);
      m.addLayer({ id: "atl-base-ln", type: "line", source: "atl-c", paint: { "line-color": surf, "line-width": 0.7 } }, first || undefined);
    }
    var B = first || undefined;
    if (M.mode === "satellite") m.addLayer({ id: "atl-c-line", type: "line", source: "atl-c", paint: { "line-color": "#ffffff", "line-opacity": 0.55, "line-width": 0.8 } });
    m.addLayer({ id: "atl-c-fill", type: "fill", source: "atl-c", paint: { "fill-color": "rgba(0,0,0,0)", "fill-opacity": ["interpolate", ["linear"], ["zoom"], 0, 0.72, 3.5, 0.55, 5.5, 0.2, 7, 0.08] } }, B);
    m.addLayer({ id: "atl-s-fill", type: "fill", source: "atl-s", layout: { visibility: "none" }, paint: { "fill-color": "rgba(0,0,0,0)", "fill-opacity": 0.5 } }, B);
    m.addLayer({ id: "atl-s-line", type: "line", source: "atl-s", layout: { visibility: "none" }, paint: { "line-color": ink, "line-opacity": 0.35, "line-width": 0.8 } }, B);
    m.addLayer({ id: "atl-c-hi", type: "fill", source: "atl-c", filter: ["==", ["get", "name"], "__none__"], paint: { "fill-color": acc, "fill-opacity": 0.4 } }, B);
    m.addLayer({ id: "atl-s-hi", type: "fill", source: "atl-s", filter: ["==", ["get", "name"], "__none__"], layout: { visibility: "none" }, paint: { "fill-color": acc, "fill-opacity": 0.4 } }, B);
    if (m.getSource("openmaptiles")) {
      var nf = ["==", ["get", "name"], "__none__"];
      m.addLayer({ id: "atl-park-fill", type: "fill", source: "openmaptiles", "source-layer": "park", filter: nf, paint: { "fill-color": acc, "fill-opacity": 0.28 } }, B);
      m.addLayer({ id: "atl-park-line", type: "line", source: "openmaptiles", "source-layer": "park", filter: nf, paint: { "line-color": acc, "line-width": 2.4 } }, B);
    }
    m.addLayer({ id: "atl-bound-fill", type: "fill", source: "atl-bound", paint: { "fill-color": acc, "fill-opacity": 0.2 } }, B);
    m.addLayer({ id: "atl-bound-line", type: "line", source: "atl-bound", layout: { "line-join": "round" }, paint: { "line-color": acc, "line-width": 2.4 } }, B);
    m.addLayer({ id: "atl-c-out", type: "fill", source: "atl-c", filter: ["==", ["get", "name"], "__none__"], paint: { "fill-color": surf, "fill-opacity": 0.5 } }, B);
    m.addLayer({ id: "atl-s-out", type: "fill", source: "atl-s", filter: ["==", ["get", "name"], "__none__"], layout: { visibility: "none" }, paint: { "fill-color": surf, "fill-opacity": 0.5 } }, B);
    m.addLayer({ id: "atl-src", type: "circle", source: "atl-src", paint: { "circle-radius": 4, "circle-color": surf, "circle-stroke-color": acc, "circle-stroke-width": 2 } });
    m.addLayer({ id: "atl-src-lb", type: "symbol", source: "atl-src", layout: { "text-field": ["get", "name"], "text-font": ["Noto Sans Italic"], "text-size": 11, "text-anchor": "left", "text-offset": [0.9, 0], "text-optional": true }, paint: { "text-color": ink, "text-halo-color": surf, "text-halo-width": 1.4 } });
    m.addLayer({ id: "atl-tie", type: "line", source: "atl-tie", layout: { "line-cap": "round" }, paint: { "line-color": acc, "line-width": 2.2, "line-dasharray": [0.1, 2.2], "line-opacity": 0.9 } });
    m.addLayer({ id: "atl-arc-hit", type: "line", source: "atl-arc", paint: { "line-color": "#000", "line-opacity": 0, "line-width": 16 } });
    m.addLayer({ id: "atl-arc", type: "line", source: "atl-arc", filter: ["==", ["get", "type"], "species"], layout: { "line-cap": "round" }, paint: { "line-color": ["case", ["==", ["get", "act"], 1], "#d0702f", acc], "line-width": 3 } });
    m.addLayer({ id: "atl-arc-flow", type: "line", source: "atl-arc", filter: ["==", ["get", "type"], "flow"], paint: { "line-color": ["case", ["==", ["get", "act"], 1], "#d0702f", acc], "line-width": 3, "line-dasharray": [2.2, 1.6] } });
    m.addLayer({ id: "atl-arc-end", type: "circle", source: "atl-al", filter: ["==", ["get", "k"], "end"], paint: { "circle-radius": 5, "circle-color": acc, "circle-stroke-color": surf, "circle-stroke-width": 1.5 } });
    m.addLayer({ id: "atl-arc-lb", type: "symbol", source: "atl-al", filter: ["==", ["get", "k"], "mid"], layout: { "text-field": ["get", "title"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-allow-overlap": true, "text-max-width": 12 }, paint: { "text-color": ink, "text-halo-color": surf, "text-halo-width": 2 } });
    m.addLayer({ id: "atl-n-pt", type: "circle", source: "atl-n", paint: { "circle-color": ["get", "kc"], "circle-radius": ["interpolate", ["linear"], ["zoom"], 0.6, 1.4, 2.4, 2.4, 3.5, DOT], "circle-stroke-color": surf, "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 0.6, 0.1, 2.4, 0.3, 3.5, 0.7], "circle-opacity": 0.9 } });
    m.addLayer({ id: "atl-cl", type: "circle", source: "atl-e", filter: ["has", "point_count"], paint: { "circle-color": acc, "circle-opacity": 0.92, "circle-radius": ["step", ["zoom"], ["step", ["get", "point_count"], 4, 10, 5, 30, 6.5], 3.5, ["step", ["get", "point_count"], 10, 10, 12, 30, 14]], "circle-stroke-color": surf, "circle-stroke-width": ["step", ["zoom"], 0.5, 3.5, 1] } });
    m.addLayer({ id: "atl-cl-n", type: "symbol", source: "atl-el", filter: ["has", "point_count"], layout: { "text-field": ["step", ["zoom"], "", 3.5, ["get", "point_count_abbreviated"]], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-allow-overlap": true }, paint: { "text-color": "#ffffff" } });
    m.addLayer({ id: "atl-pt", type: "circle", source: "atl-e", filter: ["!", ["has", "point_count"]], paint: { "circle-color": ["get", "kc"], "circle-opacity": 1, "circle-radius": ["interpolate", ["linear"], ["zoom"], 1, DOT - 1.5, 5, DOT], "circle-stroke-color": surf, "circle-stroke-width": 0.7 } });
    m.addLayer({ id: "atl-lb", type: "symbol", source: "atl-el", filter: ["!", ["has", "point_count"]], layout: { "text-field": ["get", "short"], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-variable-anchor": ["right", "left", "top", "bottom"], "text-radial-offset": 0.9, "text-justify": "auto", "text-optional": true }, paint: { "text-color": ink, "text-halo-color": surf, "text-halo-width": 1.7 } });
    m.addLayer({ id: "atl-f-pt", type: "circle", source: "atl-f", paint: { "circle-color": ["get", "kc"], "circle-radius": DOT + 3.5, "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.2 } });
    m.addLayer({ id: "atl-f-lb", type: "symbol", source: "atl-fl", layout: { "text-field": ["get", "short"], "text-font": ["Noto Sans Bold"], "text-size": 12.5, "symbol-sort-key": ["get", "pr"], "text-variable-anchor": ["right", "left", "top", "bottom"], "text-radial-offset": 1.1, "text-justify": "auto", "text-optional": true }, paint: { "text-color": ink, "text-halo-color": surf, "text-halo-width": 2 } });
    dotStyle(); if (flagMode()) m.getSource("atl-n").setData(ecoFC()); var ff = flagFC(); m.getSource("atl-f").setData(ff); m.getSource("atl-fl").setData(ff);
    m.addLayer({ id: "atl-t-ring", type: "circle", source: "atl-t", filter: ["==", ["get", "role"], "sel"], paint: { "circle-radius": 11, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    m.addLayer({ id: "atl-t-pt", type: "circle", source: "atl-t", paint: { "circle-radius": 7, "circle-color": ["get", "kc"], "circle-stroke-color": surf, "circle-stroke-width": 2 } });
    m.addLayer({ id: "atl-t-lb", type: "symbol", source: "atl-t", layout: { "text-field": ["get", "short"], "text-font": ["Noto Sans Bold"], "text-size": 12.5, "symbol-sort-key": ["case", ["==", ["get", "role"], "sel"], 0, 1], "text-variable-anchor": ["left", "right", "top", "bottom"], "text-radial-offset": 1.1, "text-justify": "auto", "text-optional": true }, paint: { "text-color": ink, "text-halo-color": surf, "text-halo-width": 2 } });
    var sat = (m.getStyle().name === "satellite");
    ["atl-lb", "atl-f-lb", "atl-t-lb"].forEach(function (l) { if (!m.getLayer(l)) return; m.setPaintProperty(l, "text-color", sat ? "#ffffff" : ink); m.setPaintProperty(l, "text-halo-color", sat ? "rgba(8,16,24,0.85)" : surf); });
  }
  function onStyle() {
    var m = M.map;
    M.styleReady = true;
    var satNow = m.getStyle().name === "satellite";
    if (satNow !== !!M.kcSat) { M.kcSat = satNow; Object.assign(KC, satNow ? KC_SAT : KC_BASE); kindsHTML(); }
    addOverlay();
    m.getContainer().classList.toggle("nobase", !!M.stub);
    if (M.boundFC) setBound(M.boundFC);
    applyTerrain(true);
    renderView(false);
    if (M.spanE) spanHi(M.spanE);
    if (M.pendingPeek) doPendingPeek();
    document.documentElement.setAttribute("data-map", "ready");
  }
  function applyTerrain(quiet) {
    var m = M.map; if (!m || !m.getSource("atl-dem")) { if (m && M.styleReady && !M.tilt && m.getPitch() > 0 && !quiet) m.easeTo({ pitch: 0, bearing: 0, duration: 500 }); return; }
    if (M.tilt) { m.setTerrain({ source: "atl-dem", exaggeration: 1.4 }); if (!quiet || m.getPitch() < 10) m.easeTo({ pitch: 58, duration: reduce ? 0 : 700 }); }
    else { m.setTerrain(null); if (!quiet) m.easeTo({ pitch: 0, bearing: 0, duration: reduce ? 0 : 500 }); }
  }
  // If the base map stops loading, quietly fall back (satellite -> streets -> plain map) and try the real one again later.
  function baseFailed(id) {
    if (M.stub) return;
    M.fails[id] = (M.fails[id] || 0) + 1;
    if (M.fails[id] < 6) return;
    M.fails = {}; M.want = M.want || M.mode;
    if ((id === "sat" || id === "sat0") && M.mode === "satellite") setMode("streets", true);
    else { M.stub = true; setMode(M.mode, true); }
    scheduleRetry();
  }
  function scheduleRetry() {
    if (M.stubUrl || M.retryTimer) return;
    var wait = window.__retryMs || [90, 300, 900][Math.min(M.retries, 2)] * 1000;
    M.retryTimer = setTimeout(function () {
      M.retryTimer = null; M.retries++; M.fails = {};
      var back = M.want || M.mode; M.want = null;
      M.stub = false; setMode(back, true);
    }, wait);
  }
  function setMode(mode, auto) {
    if (!auto) M.want = null;
    M.mode = mode; M.styleReady = false;
    M.map.setStyle(M.stub ? stubStyle() : mode === "satellite" ? satStyle() : STYLES[mode], { diff: false });
    syncCtl();
  }
  function setTilt(on) {
    M.tilt = on;
    if (on && !M.map.getSource("atl-dem")) setMode(M.mode, true); else { applyTerrain(false); syncCtl(); }
  }
  function syncCtl() {
    Array.prototype.forEach.call(document.querySelectorAll("#mapctl [data-mode]"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-mode") === M.mode ? "true" : "false"); });
    document.getElementById("tilt").setAttribute("aria-pressed", M.tilt ? "true" : "false");
  }
  function applyView() {
    var m = M.map, US_ = view.country === US && (view.level === "country" || view.level === "state");
    var F0 = ["==", ["get", "name"], "__none__"];
    function vis(id, on) { if (m.getLayer(id)) m.setLayoutProperty(id, "visibility", on ? "visible" : "none"); }
    vis("atl-s-fill", US_); vis("atl-s-line", US_); vis("atl-s-hi", US_); vis("atl-s-out", view.level === "state");
    vis("atl-c-fill", !US_); vis("atl-src", view.level === "world"); vis("atl-src-lb", view.level === "world");
    m.setFilter("atl-c-out", view.level === "continent" ? ["!=", ["get", "cont"], view.cont] : view.level === "country" ? ["!=", ["get", "name"], view.country] : view.level === "state" ? ["!=", ["get", "name"], US] : F0);
    m.setFilter("atl-s-out", view.level === "state" ? ["!=", ["get", "name"], view.state] : F0);
  }
  function shade() {
    var m = M.map; if (!m || !m.getLayer("atl-c-fill")) return;
    m.setPaintProperty("atl-c-fill", "fill-color", "rgba(0,0,0,0)"); m.setPaintProperty("atl-s-fill", "fill-color", "rgba(0,0,0,0)");
  }
  function spanHi(e) {
    M.spanE = e || null;
    var m = M.map; if (!m || !M.styleReady || !m.getLayer("atl-c-hi")) return;
    var multi = e && e.countries.length > 1;
    var cn = e && (multi || view.level !== "world") && view.level !== "state" ? e.countries : [];
    var sn = e && view.level !== "world" ? (e.states || []) : [];
    var col = e ? KC[e.kind] : "#000";
    m.setFilter("atl-c-hi", ["in", ["get", "name"], ["literal", cn]]); m.setPaintProperty("atl-c-hi", "fill-color", col);
    m.setFilter("atl-s-hi", ["in", ["get", "name"], ["literal", sn]]); m.setPaintProperty("atl-s-hi", "fill-color", col);
  }
  function curve(a, b) {
    var dx = b[0] - a[0]; if (dx > 180) b = [b[0] - 360, b[1]]; else if (dx < -180) b = [b[0] + 360, b[1]];
    dx = b[0] - a[0]; var dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len;
    if (ny < 0) { nx = -nx; ny = -ny; }
    var cx = (a[0] + b[0]) / 2 + nx * len * 0.22, cy = (a[1] + b[1]) / 2 + ny * len * 0.22, out = [];
    for (var i = 0; i <= 40; i++) { var t = i / 40, u = 1 - t; out.push([u * u * a[0] + 2 * u * t * cx + t * t * b[0], Math.max(-84, Math.min(84, u * u * a[1] + 2 * u * t * cy + t * t * b[1]))]); }
    return out;
  }
  function arcEnds(c) {
    var A, B;
    if (c.type === "species") { A = ECO_BY[c.ends[0].eco]; B = ECO_BY[c.ends[1].eco]; return [[A.lon, A.lat], [B.lon, B.lat]]; }
    if (c.from) A = [ECO_BY[c.from.eco].lon, ECO_BY[c.from.eco].lat]; else A = [SRC[c.src].lon, SRC[c.src].lat];
    B = [ECO_BY[c.to.eco].lon, ECO_BY[c.to.eco].lat];
    return [A, B];
  }
  function actOf(c) { return c.type === "species" ? c.ends.some(function (en) { return (EDITS[en.eco] || {})[en.node]; }) : !!(c.from && (EDITS[c.from.eco] || {})[c.from.node]); }
  /* outline the real park or reserve the basemap draws under the selected ecosystem */
  /* real park outlines (US: PAD-US, simplified): one small file per park, fetched when that park opens (no file = no outline) */
  var EMPTY_FC = { type: "FeatureCollection", features: [] };
  function loadBounds(id) {
    M.boundsP = M.boundsP || {};
    if (!M.boundsP[id]) M.boundsP[id] = Data.bounds(id);
    return M.boundsP[id];
  }
  function boundFC(b) {
    return { type: "FeatureCollection", features: b.r.map(function (flat) { var ring = []; for (var i = 0; i < flat.length; i += 2) ring.push([flat[i], flat[i + 1]]); return { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [ring] } }; }) };
  }
  function boundBox(b) {
    var x0 = 999, x1 = -999, y0 = 99, y1 = -99;
    b.r.forEach(function (flat) { for (var i = 0; i < flat.length; i += 2) { x0 = Math.min(x0, flat[i]); x1 = Math.max(x1, flat[i]); y0 = Math.min(y0, flat[i + 1]); y1 = Math.max(y1, flat[i + 1]); } });
    return [[x0, y0], [x1, y1]];
  }
  function setBound(fc) { M.boundFC = fc; var m = M.map; if (m && m.getSource("atl-bound")) m.getSource("atl-bound").setData(fc || EMPTY_FC); }
  function parkHi(id) {
    var m = M.map; M.parkId = id || null;
    if (!m || !M.styleReady) return;
    if (!id) setBound(null);
    if (id) {
      loadBounds(id).then(function (b) {
        if (M.parkId !== id) return;
        if (!b) { M.noBound = id; parkHiStyle(id); return; }
        setBound(boundFC(b)); M.noBound = null;
        var none = ["==", ["get", "name"], "__none__"];
        if (m.getLayer("atl-park-fill")) { m.setFilter("atl-park-fill", none); m.setFilter("atl-park-line", none); }
        if (!M.prevCam) M.prevCam = { center: m.getCenter(), zoom: m.getZoom(), bearing: m.getBearing(), pitch: m.getPitch() };
        m.fitBounds(boundBox(b), { padding: sheetMode() ? { top: 70, left: 30, right: 30, bottom: 300 } : { top: 70, left: 60, right: 60, bottom: 70 }, maxZoom: 13, duration: reduce ? 0 : 700 });
        var pe = document.getElementById("peek"), pb = pe.querySelector(".pbtns");
        if (pb && !pe.hidden && M.peekId === id && !pe.querySelector("#parkname")) { var t = document.createElement("p"); t.className = "spans"; t.id = "parkname"; t.textContent = "Outlined on the map: " + b.n; pb.parentNode.insertBefore(t, pb); }
      });
      return;
    }
    parkHiStyle(id);
  }
  function parkHiStyle(id) {
    var m = M.map;
    var have = !!m.getLayer("atl-park-fill"), none = ["==", ["get", "name"], "__none__"];
    if (have) { m.setFilter("atl-park-fill", none); m.setFilter("atl-park-line", none); }
    if (!id) return;
    var e = ECO_BY[id], zoomed = false;
    function run() {
      if (M.parkId !== id) return;
      var c = m.project([e.lon, e.lat]), f = null;
      [14, 40, 90].some(function (r) {
        var fs = m.queryRenderedFeatures([[c.x - r, c.y - r], [c.x + r, c.y + r]], { layers: ["park"] });
        f = fs.filter(function (x) { return x.properties && x.properties.name; })[0] || null;
        return !!f;
      });
      if (!f) return;
      var flt = ["==", ["get", "name"], f.properties.name];
      m.setFilter("atl-park-fill", flt); m.setFilter("atl-park-line", flt);
      var pe = document.getElementById("peek"), pb = pe.querySelector(".pbtns");
      if (pb && !pe.hidden && M.peekId === id && !pe.querySelector("#parkname")) { var t = document.createElement("p"); t.className = "spans"; t.id = "parkname"; t.textContent = "Outlined on the map: " + f.properties.name; pb.parentNode.insertBefore(t, pb); }
    }
    if (m.getZoom() < 6.5) {
      if (!M.prevCam) M.prevCam = { center: m.getCenter(), zoom: m.getZoom(), bearing: m.getBearing(), pitch: m.getPitch() };
      m.easeTo({ center: [e.lon, e.lat], zoom: 7.5, duration: reduce ? 0 : 700, padding: { bottom: sheetMode() ? 240 : 0 } });
      zoomed = true;
    }
    if (!have || !m.getLayer("park")) return;
    if (zoomed) m.once("idle", run);
    else if (m.loaded() && !m.isMoving()) run(); else m.once("idle", run);
  }
