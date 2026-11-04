  /* ---------- Data: the one place that knows where the app's data files are and how to read them (#241). Every read of a file we host goes through here; the map library, the head loader that starts the world places early, and the later steps of #241 are the only exceptions for now.
     json(url, missing): the parsed file; a 404 gives `missing` when that is given, anything else that is not a success is an error. Callers keep their own memo and error handling. ---------- */
  var Data = (function () {
    var root = location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "");
    function json(url, missing) {
      if (!window.fetch) return Promise.reject();
      return fetch(url).then(function (r) { if (r.status === 404 && missing !== undefined) return missing; if (!r.ok) throw 0; return r.json(); });
    }
    return {
      root: root,
      json: json,
      species: function (id) { return json(root + "api/species/" + id + ".json", null); },   /* a species' long description; null when it has none */
      bounds: function (id) { return json(root + "data/outlines/" + encodeURIComponent(id) + ".json").catch(function () { return null; }); },   /* a park's outline; null when missing or unreadable */
      states: function () { return json(root + "geo-states.json"); },   /* the US state outlines */
      counts: function () { return json(root + "api/places/__PLACES_DIR__/counts.json"); },   /* places per region, kind and park, written by the build (#261) */
      place: function (id) { return json(root + "api/" + id + ".json"); },   /* a place's full web (nodes, links, evidence, story, its species' picture entries) */
      speciesPlaces: function (k) { return json(root + "api/species-places__PLACES_SFX__/" + k + ".json", {}); },   /* which places a species is in; {} when there is no file */
      ties: function (k) { return json(root + "api/ties__PLACES_SFX__/" + k + ".json", {}); },   /* the ties of one region; {} when there is no file */
      search: function (f) { return json("api/search__PLACES_SFX__/" + f); },   /* a search file (meta, word bucket or rows); a page-relative address, as before */
      pictures: function () { return json(root + "api/species-pictures.json"); },   /* every hosted species picture with its credit */
      placePhotos: function () { return json(root + "photos/places/places.json").catch(function () { return {}; }); }   /* the stored place photos; {} when missing */
    };
  })();
  // A species' long description is its own small file, api/species/<id>.json, fetched when its sheet opens (no file for a species without one).
  function loadAbout(n) {
    var id = sidOf(n);
    if (!(id in ABOUT_P)) ABOUT_P[id] = Data.species(id).then(function (a) { ABOUT[id] = a && a.t || null; return true; }).catch(function () { delete ABOUT_P[id]; return false; });
    return ABOUT_P[id];
  }
  function aboutHTML(n) {
    if (!n.latin) return "";
    var id = sidOf(n);
    if (id in ABOUT) { var t = aboutText(n); return t ? '<p class="about">' + t + "</p>" : ""; }
    loadAbout(n).then(function (ok) {
      var el = ok && document.querySelector('.about[data-lat="' + id + '"]');
      if (!el) return;
      var t = aboutText(n); if (t) el.innerHTML = t; else el.remove();
    });
    return '<p class="about" data-lat="' + id + '"></p>';
  }
  /* Places: the one way to read them. The index (map, filters, regions) and the cards (names and text) arrive as two files; each place is the two put together.
     The page starts with the world-level places; the local places (NLOCAL of them, hidden unless the local button is on or a search is typed) are fetched after the map has drawn,
     or at once when something needs them (the local button, a search, Near me, a link to one). Places.done is true when they are in. */
  var NLOCAL = __NLOCAL__;
  function join(PLx) { return PLx[0].map(function (i) { var c = PLx[1][i.id]; for (var k in c) i[k] = c[k]; return i; }); }
  var ECOS = join(PL);
  var Places = {
    all: function () { return ECOS; }, get: function (id) { return ECO_BY[id]; },
    done: !NLOCAL || !!window.__LOCALS_IN, nLocal: NLOCAL, total: ECOS.length + (window.__LOCALS_IN ? 0 : NLOCAL), p: null, failedAt: 0,
    loadLocals: function () {
      if (Places.done) return Promise.resolve(true);
      if (Places.p) return Places.p;
      if (Places.failedAt && Date.now() - Places.failedAt < 30000) return Promise.resolve(false);
      Places.p = window.__LOCALS().then(function (r) {
        var add = join(r);
        add.forEach(function (e) { ECOS.push(e); ECO_BY[e.id] = e; addEcoOption(e); });
        Places.done = true;
        if (FL.local || FL.q) { M.pgKey = null; filterView(); }   /* only then are the new places on the screen */
        return true;
      }).catch(function () { Places.p = null; Places.failedAt = Date.now(); return false; });
      return Places.p;
    }
  };
  /* Related places and the places of a species come from the build, not from a scan of every place: a place file carries rel (relp on the pilot page),
     api/species-places/<first two letters>.json lists the places of each species found in two or more places (items #252, #253). */
  var PILOT = "__PLACES_DIR__" === "pilot", SPPL = { f: {}, d: {} };
  function sppBucket(l) { return (l.toLowerCase().replace(/[^a-z0-9]/g, "") + "__").slice(0, 2); }
  function sppFile(l) {
    var k = sppBucket(l);
    if (!SPPL.f[k]) SPPL.f[k] = Data.speciesPlaces(k).catch(function () { SPPL.f[k] = null; return {}; });
    return SPPL.f[k];
  }
  /* a promise of the ids of the places that list the species (this one too), in page order; the local places it names are loaded first when they are not yet */
  function sppPlaces(l) {
    return sppFile(l).then(function (d) {
      var ids = d[l] || [];
      return (!Places.done && ids.some(function (i) { return !ECO_BY[i]; }) ? Places.loadLocals() : Promise.resolve()).then(function () { if (SPPL.f[sppBucket(l)]) SPPL.d[l] = ids; return ids; });
    });
  }
  function relatedFor(e, n) { return (e.rel || []).filter(function (x) { return ECO_BY[x[0]]; }).slice(0, n).map(function (x) { return { e: ECO_BY[x[0]], c: x[1] }; }); }
  /* Search reads the ready-made word index (api/search/, written by the build, item #260): each query word is looked up by prefix in one small file named by its
     first two letters, and a place is a match when every word finds it. Place numbers are positions in ECOS (same page order). Until the files have arrived the
     list filters on the card text alone; if they cannot be had, the list stays on the card text alone and the index is tried again after 30 s. */
  var SRCH = { failedAt: 0, meta: null, bk: {}, rows: {} };
  function srchGet(f) { return Data.search(f); }
  function srchWords(t) { return t.toLowerCase().replace(/['\u2019]/g, "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").split(/[^a-z0-9]+/).filter(function (w) { return w.length > 0; }); }
  function srchBucket(k) {
    if (!SRCH.bk[k]) SRCH.bk[k] = srchGet("w-" + k + ".json");
    return SRCH.bk[k];
  }
  /* the place numbers of every word that starts with w (a Set) */
  function srchPrefix(b, w) {
    var lo = 0, hi = b.w.length, out = new Set();
    while (lo < hi) { var mid = (lo + hi) >> 1; if (b.w[mid] < w) lo = mid + 1; else hi = mid; }
    for (var i = lo; i < b.w.length && b.w[i].lastIndexOf(w, 0) === 0; i++) { var t = 0; b.p[i].forEach(function (d) { t += d; out.add(t); }); }
    return out;
  }
  /* the id of place number n (its position in the full list) is in the rows files: 256 places each, [id, name, place, lat, lon, continent, state] */
  function srchRows(k) { return SRCH.rows[k] || (SRCH.rows[k] = srchGet("rows-" + k + ".json")); }
  function srchRun(q) {
    var ws = srchWords(q).filter(function (w) { return w.length >= 2; });
    if (!ws.length || (SRCH.failedAt && Date.now() - SRCH.failedAt < 30000)) return Promise.resolve(null);
    if (!SRCH.meta) SRCH.meta = srchGet("meta.json");
    return Promise.all([SRCH.meta, Places.loadLocals()]).then(function (r) {
      var m = r[0];
      if (!r[1] || m.n !== Places.total) throw 0;   /* not the same list as the page, or the local places did not come: do not trust the numbers */
      return Promise.all(ws.map(function (w) { return m.buckets.indexOf(w.slice(0, 2)) < 0 ? new Set() : srchBucket(w.slice(0, 2)).then(function (b) { return srchPrefix(b, w); }); })).then(function (sets) {
        sets.sort(function (a, b) { return a.size - b.size; });
        var nums = []; sets[0].forEach(function (n) { if (sets.every(function (x) { return x.has(n); })) nums.push(n); });
        var ks = []; nums.forEach(function (n) { var k = Math.floor(n / m.rows); if (ks.indexOf(k) < 0) ks.push(k); });
        return Promise.all(ks.map(srchRows)).then(function (files) {
          var by = {}; ks.forEach(function (k, i) { by[k] = files[i]; });
          var hits = new Set();
          nums.forEach(function (n) { var row = by[Math.floor(n / m.rows)][n % m.rows]; if (row && ECO_BY[row[0]]) hits.add(row[0]); });
          return hits;
        });
      });
    }).catch(function () { SRCH.failedAt = Date.now(); SRCH.meta = null; return null; });
  }
  /* a typed query: filter on the card text at once, then on the index when it arrives */
  function searchFor(q) {
    FL.hits = null;
    if (!q) return;
    srchRun(q).then(function (hits) {
      if (FL.q !== q) return;
      if (hits) FL.hits = hits;
      M.pgKey = null; filterView();
    });
  }
  var COUPLE = DATA.couple;
  var SRC = DATA.src;
  var CROSS = DATA.cross;
  var ECO_BY = {};
  ECOS.forEach(function (e) { ECO_BY[e.id] = e; });
  /* Shared-species ties between places (the map arcs and the line on a map card): api/ties[-pilot]/<region>.json, one file per region (the region place files'
     grouping: world, a US state or a continent), fetched on the first tap in that region (item #252). A place has its 16 closest places, the first 5 with the
     number of shared species and up to 3 of their names. */
  var TIESD = { f: {}, d: {}, lw: false };
  function slugOf(t) { return t.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, ""); }
  function tieRegion(e) { return e.level === "local" ? slugOf(e.countries.indexOf("United States of America") >= 0 && e.states && e.states.length ? e.states[0] : e.conts[0]) : "world"; }
  function loadTies(k) {
    if (!TIESD.f[k]) TIESD.f[k] = Data.ties(k).then(function (d) {
      TIESD.d[k] = d; refreshArcs(); if (M.peekId) fillPeekTies(M.peekId); return true;
    }).catch(function () { TIESD.f[k] = null; return false; });
    return TIESD.f[k];
  }
  function tiesFor(id) {
    var e = ECO_BY[id], k = tieRegion(e), d = TIESD.d[k];
    if (!d) { loadTies(k); return []; }
    var rows = d[id] || [], out = rows.filter(function (r) { return ECO_BY[typeof r === "string" ? r : r[0]]; });
    if (out.length < rows.length && !Places.done && !TIESD.lw) { TIESD.lw = true; Places.loadLocals().then(function (ok) { if (ok) { refreshArcs(); if (M.peekId) fillPeekTies(M.peekId); } }); }   /* a local place the list names is not loaded yet */
    return out.map(function (r) { return typeof r === "string" ? { eco: r, spp: null } : { eco: r[0], spp: r[2], n: r[1] }; });
  }
  var XL = {};
  CROSS.forEach(function (c) {
    if (c.type === "species") {
      [0, 1].forEach(function (i) { var a = c.ends[i], b = c.ends[1 - i]; (XL[a.eco] = XL[a.eco] || {})[a.node] = { link: c, other: b }; });
    } else if (c.from) {
      (XL[c.to.eco] = XL[c.to.eco] || {})[c.to.node] = { link: c, other: c.from, dir: "in" };
      (XL[c.from.eco] = XL[c.from.eco] || {})[c.from.node] = { link: c, other: c.to, dir: "out" };
    } else { (XL[c.to.eco] = XL[c.to.eco] || {})[c.to.node] = { link: c, other: null }; }
  });
  var EDITS = {};
  var KIND = { s: "scav", r: "res", d: "det" };

