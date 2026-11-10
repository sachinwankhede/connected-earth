  /* closing the card takes the map back to where it was before the tap */
  function restoreCam() {
    var m = M.map, c = M.prevCam; M.prevCam = null;
    if (!m || !c) return;
    m.easeTo({ center: c.center, zoom: c.zoom, bearing: c.bearing, pitch: c.pitch, padding: { bottom: 0 }, duration: reduce ? 0 : 700 });
  }
  function showTies(id, soft) { M.tieId = id || null; M.soft = !!soft; pushTies(); }
  function pushTies() {
    var m = M.map; if (!m || !M.styleReady || !m.getSource("atl-t")) return;
    var id = M.tieId, on = tieOn(id), tf = [], ties = [], arcs = [], al = [];
    if (id) {
      Object.keys(on).forEach(function (k) { tf.push(pt(ECO_BY[k], { role: k === id ? "sel" : "tie" })); });
      var a = [ECO_BY[id].lon, ECO_BY[id].lat];
      tiesFor(id).filter(function (t) { return inRegion(ECO_BY[t.eco]); }).slice(0, 8).forEach(function (t) { var o = ECO_BY[t.eco]; ties.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: curve(a, [o.lon, o.lat]) } }); });
      if (!M.soft) CROSS.forEach(function (c) {
        if (!ecoEnds(c).some(function (en) { return en.eco === id; })) return;
        var ab = arcEnds(c), cv = curve(ab[0], ab[1]);
        arcs.push({ type: "Feature", properties: { id: c.id, type: c.type, act: actOf(c) ? 1 : 0 }, geometry: { type: "LineString", coordinates: cv } });
        al.push({ type: "Feature", properties: { k: "mid", title: c.title }, geometry: { type: "Point", coordinates: cv[20] } });
        if (c.type === "flow") al.push({ type: "Feature", properties: { k: "end" }, geometry: { type: "Point", coordinates: cv[40] } });
      });
    }
    function fc(f) { return { type: "FeatureCollection", features: f }; }
    m.getSource("atl-t").setData(fc(tf)); try { m.setFilter("atl-lb", ["all", ["!", ["has", "point_count"]], ["!", ["in", ["get", "id"], ["literal", tf.map(function (f) { return f.properties.id; })]]]]); } catch (x) {} m.getSource("atl-tie").setData(fc(ties)); m.getSource("atl-arc").setData(fc(arcs)); m.getSource("atl-al").setData(fc(al));
    var f = id ? 0.28 : 1;
    m.setPaintProperty("atl-pt", "circle-opacity", f); m.setPaintProperty("atl-pt", "circle-stroke-opacity", f); m.setPaintProperty("atl-lb", "text-opacity", f); m.setPaintProperty("atl-f-pt", "circle-opacity", f); m.setPaintProperty("atl-f-pt", "circle-stroke-opacity", f); m.setPaintProperty("atl-f-lb", "text-opacity", f);
  }
  function refreshArcs() { pushTies(); }
  var PITCH = "See how nature is connected", PITCH2 = "What eats what, and where it travels";
  function filterView() {
    renderView(false);
    var m = M.map; if (!m || !M.styleReady) return;
    var bd = m.getBounds(), any = ECOS.some(function (e) { return inRegion(e) && bd.contains([e.lon, e.lat]); });
    if (!any && ECOS.some(inRegion)) mapFit(true);
  }
  function renderView(animate) {
    var m = M.map;
    if (m && M.styleReady && m.getSource("atl-e")) {
      applyView(); shade();
      setEco();
      if (animate || M.needFit) mapFit(animate);
      pushTies();
    }
    kindsHTML();
    var list = ECOS.filter(inRegion);
    var pgKey = [view.level, view.cont, view.country, view.state, FL.q, FL.kind, FL.park].join("|");
    if (M.pgKey !== pgKey) { M.pgKey = pgKey; var nv = list.length; M.pageN = nv <= 12 ? nv : 10; }
    var pm = window.matchMedia && matchMedia("(max-width: 700px)").matches, shown = 0, left = 0;
    /* on a phone only the shown cards are built; "Show more" or scrolling builds the rest */
    var dom = false; list.forEach(function (e, i) { if (pm && i >= M.pageN) return; makeCard(e); if (!e.li.parentNode) dom = true; });
    if (dom) { var mo0 = document.getElementById("morecards"), inl = new Set(list), kids = ECOS.filter(function (e) { return e.li && (e.li.parentNode || inl.has(e)); }).map(function (e) { return e.li; }); if (mo0) kids.push(mo0); document.getElementById("cards").replaceChildren.apply(document.getElementById("cards"), kids); }
    ECOS.forEach(function (e) { if (e.li) e.li.hidden = true; }); list.forEach(function (e) { if (e.li) e.li.hidden = false; });
    qHead();   /* the result header (#425) */
    list.forEach(function (e) { shown++; if (pm && shown > M.pageN) { left++; if (e.li) e.li.classList.add("pg"); } else if (e.li) e.li.classList.remove("pg"); });
    if (!M.moreIO && window.IntersectionObserver) {
      M.moreIO = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting && M.scrolled && M.pageN) { M.moreIO.unobserve(en.target); M.pageN += 15; renderView(false); } }); }, { rootMargin: "0px 0px 120px 0px" });
      var sb2 = document.getElementById("sbody"); if (sb2) sb2.addEventListener("scroll", function () { M.scrolled = true; }, { passive: true });
    }
    if (M.pgKey2 !== pgKey) { M.pgKey2 = pgKey; M.scrolled = false; }
    var mo = document.getElementById("morecards"); if (!mo) { mo = document.createElement("li"); mo.id = "morecards"; mo.className = "morerow"; document.getElementById("cards").appendChild(mo); }
    mo.hidden = !(pm && left > 0); mo.innerHTML = '<button type="button" class="moretxt" id="more">Show ' + Math.min(left, 15) + ' more places &rsaquo;</button>';
    if (!mo.hidden && M.moreIO) { M.moreIO.unobserve(mo); M.moreIO.observe(mo); }
    var fb = document.getElementById("fbtn"); if (fb) fb.classList.toggle("on", !!(FL.kind || FL.park));
    document.getElementById("xwrap").hidden = false;
    var em = document.getElementById("empty");   /* a search with nothing found is said once, in the note under the tabs */
    if (!FL.q) em.textContent = "No ecosystems here yet. Shaded regions on the map have food webs.";
    em.hidden = !!FL.q || list.length > 0;
    document.getElementById("crumbs").innerHTML = crumbHTML(); M.nPlaces = shown;
    if (M.tab !== "species") { document.getElementById("regions").innerHTML = chipsHTML(); kfade(); }   /* the Species tab owns this row: a redraw of the places list (Back, return to the app, local places loaded) must not blank its pills (#592) */
    var region = view.state || (view.country && nm(view.country)) || view.cont;
    if (el.webview.hidden) {
      var mt = FL.q ? list.length + (list.length === 1 ? " place matches " : " places match ") + "“" + FL.q + "”" + (view.level === "world" ? "" : " in " + region) : view.level === "world"
        ? ""   /* the home view shows the pitch below; the places-and-species count that used to be computed here was always replaced by it */
        : list.length + (list.length === 1 ? " place" : " places") + " in " + region;
      el.stats.hidden = !!FL.q;   /* a search says it in the note under the tabs */
      el.stats.textContent = FL.q && FL.busy ? "Searching…" : mt + (FL.q && FL.limited ? " · Search is limited right now" : "");   /* the query stays in the line inside a region; a failed index says so (#414) */
    }
    var hk = document.getElementById("hook");
    if (hk) { var home = view.level === "world" && !FL.q; hk.hidden = !home; if (home) hk.innerHTML = '<span class="pitch">' + PITCH + '</span><span class="stat">' + PITCH2 + "</span>"; }
    if (el.webview.hidden && view.level === "world" && !FL.q) el.stats.innerHTML = '<span class="pitch">' + PITCH + "</span>" + PITCH2;
    var spk = document.getElementById("speek");
    if (spk) {
      var f1 = view.level === "world" && !FL.q && !FL.kind && !FL.park ? list[0] : null;
      spk.hidden = !f1;
      if (f1) { var cb = cimg(f1.id); spk.innerHTML = '<span class="pimg" id="cp-' + f1.id + '">' + (cb ? cb.innerHTML : "") + '</span><span class="st"><small>Start here</small><b>' + f1.name + '</b></span><svg class="chev" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 15l6-6 6 6"/></svg>'; }
      if (!spk._b) { spk._b = 1; spk.addEventListener("click", function () { if (M.setSheet) M.setSheet("half"); }); }
    }
    M.statsHTML = el.stats.innerHTML; M.region = region;
    tabCount("places", FL.q && !FL.busy ? list.length : null);   /* after statsHTML: applyJ (below) redraws the count line */
    var sr = document.getElementById("srow");
    if (sr) {
      var par = view.level !== "world";
      M.nPlaces = shown; if (M.mapN) M.mapN();
      var cnt = shown + (shown === 1 ? " place" : " places"); sr.classList.toggle("home", view.level === "world" && !FL.q); sr.classList.toggle("q", !!FL.q);
      var anc = [];
      if (par) { anc.push(["world", "", "World"]); if (view.level !== "continent") anc.push(["continent", view.cont, view.cont]); if (view.level === "state") anc.push(["country", view.country, nm(view.country)]); }
      sr.classList.toggle("trail", par); sr.classList.toggle("deep", anc.length >= 3);
      sr.innerHTML = (par ? '<span class="strl">' + anc.map(function (x) { return '<button type="button" class="sbk" data-go="' + x[0] + '" data-a="' + String(x[1]).replace(/"/g, "&quot;") + '">' + x[2] + '</button><span class="sep" aria-hidden="true">\u203a</span>'; }).join("") + "</span>" : "") + '<span class="stt">' + (par ? region : "Connected Earth") + '</span><span class="scnt">' + cnt + "</span>";
    }
    var sr3 = document.getElementById("srow"); if (sr3) { M.srHTML = sr3.innerHTML; M.srHome = sr3.classList.contains("home"); }
    applyJ();
    syncHash();
  }
  function hashState() {
    var s = document.getElementById("q").value.trim(), pre = s ? "s=" + encodeURIComponent(s) : "";   /* the search comes first: r= takes the rest of the address (#412) */
    function part(x) { return pre && x ? pre + "&" + x : pre || x; }
    if (M.jid) return part("j=" + M.jid);
    if (M.pid) return part("pg=" + M.pid);
    if (M.sid) return part("sp=" + M.sid);
    if (!el.webview.hidden) return part("e=" + el.eco.value);
    if (!document.getElementById("peek").hidden && M.peekId) return part("p=" + M.peekId);
    if (view.level === "continent") return part("r=continent:" + view.cont);
    if (view.level === "country") return part("r=country:" + view.country);
    if (view.level === "state") return part("r=state:" + view.state);
    return part("");
  }
  function syncHash() {
    try {
      var h = hashState(); h = (/(^|[#&])stub/.test(M.h0 || "") ? "stub" + (h ? "&" : "") : "") + h;
      var hh = h ? encodeURI(h) : "", url = location.pathname + location.search + (hh ? "#" + hh : "");
      if (M.pushNext) { M.pushNext = false; if (location.hash.slice(1) !== hh) { history.pushState({ sp: M.pid || M.sid ? 1 : 0 }, "", url); return; } }   /* a new step the Back key can undo: a search starts, a place opens from a search (sp: the place's own entry) */
      history.replaceState(M.pid || M.sid || M.fromHash ? history.state : null, "", url);   /* the marker stays while the address is being applied (the place is not shown yet) */
    } catch (e) {}
  }
  function doPendingPeek() {
    var id = M.pendingPeek; M.pendingPeek = null;
    if (!ECO_BY[id]) return;
    M.needFit = false;
    M.map.jumpTo({ center: [ECO_BY[id].lon, ECO_BY[id].lat], zoom: 5 });
    peek(id);
  }
  function applyHash(h0) {
    var h = ""; try { h = decodeURIComponent(typeof h0 === "string" ? h0 : location.hash.slice(1)); } catch (e) {}
    var m, want = /(?:^|&)(?:pg|e|p)=([\w-]+)/.exec(h);
    if (want && !ECO_BY[want[1]] && !Places.done) { Places.loadLocals().then(function (ok) { if (ok) applyHash(h0); }); return; }   /* a link to a local place: they come first */
    M.fromHash = true;   /* what the address opens is not a new step */
    var sm = /(?:^|&)s=([^&]*)/.exec(h), sq = ""; if (sm) { try { sq = decodeURIComponent(sm[1]); } catch (e) { sq = sm[1]; } }
    if (sq.toLowerCase() !== (FL.q || "") || sq !== document.getElementById("q").value.trim()) runSearch(sq);   /* an address brings its own search or clears it; a reload restores the box text before the search runs */
    if ((m = /(?:^|&)j=([\w-]+)/.exec(h)) && jbyId(m[1])) showJourney(m[1]);
    else if ((m = /(?:^|&)pg=([\w-]+)/.exec(h)) && ECO_BY[m[1]]) showPlace(m[1]);
    else if ((m = /(?:^|&)sp=([\w-]+)/.exec(h))) showSpecies(m[1]);
    else if ((m = /(?:^|&)e=([\w-]+)/.exec(h)) && ECO_BY[m[1]]) showWeb(m[1]);
    else if ((m = /(?:^|&)p=([\w-]+)/.exec(h)) && ECO_BY[m[1]]) { M.pendingPeek = m[1]; if (M.styleReady) doPendingPeek(); }
    else if ((m = /(?:^|&)r=(\w+):(.+)$/.exec(h))) {
      if (m[1] === "continent" && CONT_BOX[m[2]]) go("continent", m[2]);
      else if (m[1] === "country" && M.countryBy[m[2]]) go("country", m[2]);
      else if (m[1] === "state") { var sn = m[2]; ensureStates().then(function () { if (M.stateBy[sn]) go("state", sn); }); }
    }
    else if (typeof h0 !== "string" && (M.pid || M.sid) && !/(?:^|&)(?:pg|sp|e|p|j)=/.test(h)) showMap();   /* Back from a place that was opened from a search: the address has no place any more */
    M.fromHash = false;
  }
  document.addEventListener("click", function (ev) { var b = ev.target.closest(".shbtn"); if (b) { ev.stopPropagation(); share(b); } }, true);
  function toast(t) { var v = document.getElementById("vtoast"); if (!v) return; v.textContent = t; v.classList.add("on"); clearTimeout(v._t); v._t = setTimeout(function () { v.classList.remove("on"); }, 1600); }
  function share(btn) {
    syncHash();
    var url = location.href.replace(/#stub&?/, "#").replace(/#$/, "");
    function flash(t) { if (btn.id === "share") { toast(t); return; } if (btn.classList.contains("ibtn")) { btn.classList.add("done"); btn.setAttribute("aria-label", t); setTimeout(function () { btn.classList.remove("done"); btn.setAttribute("aria-label", "Share link"); }, 1600); return; } var o = btn.textContent; btn.textContent = t; setTimeout(function () { btn.textContent = o; }, 1600); }
    if (navigator.share) { navigator.share({ title: document.title, url: url }).catch(function () {}); return; }
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { flash("Link copied"); }, function () { flash("Copy failed"); });
  }
  function nearMe() {
    var pe = document.getElementById("peek");
    if (!Places.done) { pe.innerHTML = '<div class="nearlist"><div class="nhead"><h2>Near you</h2>' + ICON_CLOSE + '</div><p>Finding places…</p></div>'; pe.hidden = false; Places.loadLocals().then(function (ok) { if (ok) nearMe(); }); return; }
    function msg(t) { M.peekId = null; pe.innerHTML = '<div class="nearlist"><div class="nhead"><h2>Near you</h2>' + ICON_CLOSE + '</div><p>' + t + '</p></div>'; pe.hidden = false; }
    if (!navigator.geolocation) { msg("This browser can't share your location."); return; }
    msg("Finding your location…");
    navigator.geolocation.getCurrentPosition(function (pos) {
      var la = pos.coords.latitude, lo = pos.coords.longitude, R = Math.PI / 180;
      function dist(e) { var a = Math.pow(Math.sin((e.lat - la) * R / 2), 2) + Math.cos(la * R) * Math.cos(e.lat * R) * Math.pow(Math.sin((e.lon - lo) * R / 2), 2); return 12742 * Math.asin(Math.sqrt(a)); }
      var mi = /^en-US/i.test(navigator.language || ""), list = ECOS.filter(function (e) { var l = FL.local; FL.local = true; var r = pass(e); FL.local = l; return r; }).map(function (e) { return { e: e, d: dist(e) }; }).sort(function (a, b) { return a.d - b.d; }).slice(0, 5);
      function fmt(d) { var v = mi ? d * 0.621371 : d; return (v < 10 ? v.toFixed(1) : Math.round(v).toLocaleString()) + (mi ? " mi" : " km"); }
      view = { level: "world", cont: null, country: null, state: null }; M.tieId = null; spanHi(null);
      if (M.userMk) M.userMk.remove();
      var dot = document.createElement("div"); dot.className = "me";
      M.userMk = new maplibregl.Marker({ element: dot }).setLngLat([lo, la]).addTo(M.map);
      M.peekId = null;
      pe.innerHTML = '<div class="nearlist"><div class="nhead"><h2>Nearest food webs</h2>' + ICON_CLOSE + '</div>' + list.map(function (x) { return '<button type="button" class="nrow" data-peek="' + x.e.id + '"><b>' + x.e.short + '</b><span>' + fmt(x.d) + '</span></button>'; }).join("") + '</div>';
      pe.hidden = false;
      renderView(false);
      var b = new maplibregl.LngLatBounds([lo, la], [lo, la]);
      list.slice(0, 3).forEach(function (x) { b.extend([x.e.lon, x.e.lat]); });
      M.map.fitBounds(b, { padding: { top: 70, left: 50, right: 50, bottom: sheetMode() ? 260 : 60 }, maxZoom: 9, duration: reduce ? 0 : 900 });
    }, function () { msg("Couldn't get your location. Allow location access for this site in your browser settings, then try again."); }, { timeout: 10000, maximumAge: 600000 });
  }
  function initMap() {
    var box = document.getElementById("map");
    if (!window.maplibregl) { box.innerHTML = '<p class="fine" style="padding:16px">The map library did not load. The ecosystem cards below still work.</p>'; return; }
    var m = M.map = new maplibregl.Map({ container: "map", style: M.stub ? stubStyle() : M.mode === "satellite" ? satStyle() : STYLES[M.mode], center: [10, 25], zoom: box.clientWidth < 560 ? 0.6 : 1.2, minZoom: 0.6, maxZoom: 17, renderWorldCopies: false, maxPitch: 75, fadeDuration: 120, attributionControl: { compact: true } });
    setTimeout(function () { var at = document.querySelector(".maplibregl-ctrl-attrib"); if (at) at.classList.remove("maplibregl-compact-show"); }, 600);
    (function () {
      var bt = document.getElementById("boot");
      if (!bt) return;
      var done = function () { if (!bt.parentNode) return; bt.classList.add("gone"); setTimeout(function () { if (bt.parentNode) bt.parentNode.removeChild(bt); }, 450); };
      m.once("idle", done); m.once("load", done); setTimeout(done, 7000);   /* the start screen never stays if the map is slow, blocked or offline */
    })();
    var mh = M.mapHooks || []; M.mapHooks = []; mh.forEach(function (f) { f(); });
    window._atlas = M;
    document.getElementById("map").parentNode.appendChild(document.getElementById("peek"));
    m.on("style.load", onStyle);
    m.on("error", function (ev) {
      if (window._mlerr) window._mlerr.push(String(ev.error && ev.error.message).slice(0, 160));
      if (!M.styleReady && !M.stub) { M.stub = true; M.styleFail = true; M.want = M.want || M.mode; m.setStyle(stubStyle(), { diff: false }); scheduleRetry(); }
      else if (M.styleReady && (ev.sourceId === "sat" || ev.sourceId === "sat0" || ev.sourceId === "openmaptiles")) baseFailed(ev.sourceId);
    });
    m.on("data", function (ev) { if (ev.dataType === "source" && ev.tile && M.fails[ev.sourceId]) M.fails[ev.sourceId] = 0; });
    var pop = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12, className: "ecopop" });
    var touch = window.matchMedia && matchMedia("(pointer: coarse)").matches;
    function hit(ev, ids, pad) {
      ids = ids.filter(function (l) { return m.getLayer(l) && !(l === "atl-pt" && flagMode()); });
      if (!ids.length) return [];
      if (touch && pad) pad = Math.max(pad, 22);
      var p = ev.point, fs = m.queryRenderedFeatures([[p.x - pad, p.y - pad], [p.x + pad, p.y + pad]], { layers: ids });
      if (pad && fs.length > 1 && fs[0].geometry.type === "Point") {
        /* with a fat finger several dots can be in reach: take the nearest one */
        var best = null, bd = 1e9;
        fs.forEach(function (f) { var c = m.project(f.geometry.coordinates), d = Math.hypot(c.x - p.x, c.y - p.y); if (d < bd) { bd = d; best = f; } });
        return [best];
      }
      return fs;
    }
    m.on("click", function (ev) {
      if (sheetMode()) { if (M.setSheet && M.sheetState !== "min") M.setSheet("min"); var mbx = document.querySelector(".mapbox"); if (mbx) mbx.classList.remove("lopen"); }
      if (sheetMode() && !document.getElementById("peek").hidden && !hit(ev, ["atl-t-pt", "atl-f-pt", "atl-pt", "atl-cl"], 9).length && !hit(ev, ["atl-arc-hit"], 6).length) { document.getElementById("peek").hidden = true; spanHi(null); showTies(null); return; }
      var f = hit(ev, ["atl-t-pt", "atl-f-pt", "atl-pt"], 9);
      if (f.length) { var id = f[0].properties.id; pop.remove(); peek(id); return; }
      f = hit(ev, ["atl-cl"], 4);
      if (f.length) { m.getSource("atl-e").getClusterExpansionZoom(f[0].properties.cluster_id).then(function (z) { m.easeTo({ center: f[0].geometry.coordinates, zoom: Math.min(z + 0.4, 12), duration: reduce ? 0 : 600 }); }); return; }
      f = hit(ev, ["atl-arc-hit"], 6);
      if (f.length) { showJourney(f[0].properties.id); return; }
      if (flagMode()) { var nb = m.queryRenderedFeatures([[ev.point.x - 22, ev.point.y - 22], [ev.point.x + 22, ev.point.y + 22]], { layers: ["atl-n-pt"] }); if (nb.length) { m.easeTo({ center: ev.lngLat, zoom: Math.min(m.getZoom() + 1.4, 3.6), duration: reduce ? 0 : 500 }); return; } }
      f = hit(ev, ["atl-s-fill", "atl-c-fill"], 0);
      if (f.length && f[0].layer.id === "atl-s-fill" && view.level === "country") { go("state", f[0].properties.name); return; }
      if (f.length && f[0].layer.id === "atl-c-fill") {
        var p = f[0].properties;
        if (view.level === "world") go("continent", p.cont);
        else if (view.level === "continent" && p.cont === view.cont) go("country", p.name);
      }
    });
    m.on("mousemove", function (ev) {
      var f = hit(ev, ["atl-t-pt", "atl-f-pt", "atl-pt"], 7), c = f.length ? f : hit(ev, ["atl-cl", "atl-arc-hit"], 5);
      m.getCanvas().style.cursor = c.length ? "pointer" : "";
      if (f.length) {
        var id = f[0].properties.id;
        if (M.hov !== id && document.getElementById("peek").hidden) { M.hov = id; spanHi(ECO_BY[id]); showTies(id, true); }
      } else { if (M.hov) { M.hov = null; if (document.getElementById("peek").hidden) { spanHi(null); showTies(null); } } }
    });
    (function () { var cm = document.getElementById("credmodal"); function cl() { cm.hidden = true; }
      document.getElementById("credbtn").addEventListener("click", function () { cm.hidden = false; document.getElementById("credx").focus(); });
      document.getElementById("credx").addEventListener("click", cl);
      cm.addEventListener("click", function (ev) { if (ev.target === cm) cl(); });
      addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !cm.hidden) { cl(); ev.stopImmediatePropagation(); } }, true); })();
    addEventListener("keydown", function (ev) {
      var pk = document.getElementById("peek");
      if (ev.key === "Escape" && !el.mapview.hidden && !pk.hidden) { pk.hidden = true; spanHi(null); showTies(null); }
    });
    document.getElementById("znear").addEventListener("click", nearMe);
    document.getElementById("share").addEventListener("click", function () { share(this); });
    document.getElementById("peek").addEventListener("click", function (ev) { var b = ev.target.closest("[data-share]"); if (b) { share(b); return; } if (ev.target.closest("button, a, [data-peek]")) return; var go = document.getElementById("peek").querySelector("[data-open]"); if (go) go.click(); });
    new MutationObserver(function () { syncHash(); if (document.getElementById("peek").hidden) { parkHi(null); restoreCam(); } }).observe(document.getElementById("peek"), { attributes: true, attributeFilter: ["hidden"], childList: true });
    document.getElementById("mapview").addEventListener("click", function (ev) {
      var mb = ev.target.closest("#more"); if (mb) { M.pageN += 15; renderView(false); return; }
      var fb = ev.target.closest("#fbtn"); if (fb) { var o = this.classList.toggle("fopen"); fb.setAttribute("aria-expanded", o); return; }
      var sb = ev.target.closest(".sbk"); if (sb) { go(sb.getAttribute("data-go"), sb.getAttribute("data-a")); return; }
      var lb = ev.target.closest("#lyrbtn"); if (lb) { var mbx = document.querySelector(".mapbox"), lo = mbx.classList.toggle("lopen"); lb.setAttribute("aria-expanded", lo); return; }
      if (ev.target.closest("#mapctl [data-mode], #tilt")) document.querySelector(".mapbox").classList.remove("lopen");
      var hb = ev.target.closest("#hbtn"); if (hb) { var o2 = this.classList.toggle("hopen"); hb.setAttribute("aria-expanded", o2); }
    });
    (function () {
      var sh = document.getElementById("sheet"), hd = document.getElementById("shead"); if (!sh || !hd) return;
      var st = "min", sy = 0, h0 = 0, moved = false, drag = false;
      function setS(s) { st = s; sh.classList.remove("s-min", "s-half", "s-full"); sh.classList.add("s-" + s); sh.style.height = ""; M.sheetState = s; }
      M.setSheet = setS; M.sheetState = "min";
      hd.addEventListener("pointerdown", function (e) { if (e.target.closest("button")) return; drag = true; moved = false; sy = e.clientY; h0 = sh.getBoundingClientRect().height; sh.classList.add("drag"); try { hd.setPointerCapture(e.pointerId); } catch (x) {} });
      hd.addEventListener("pointermove", function (e) { if (!drag) return; var dy = e.clientY - sy; if (Math.abs(dy) > 4) moved = true; sh.style.height = Math.max(64, Math.min(innerHeight - 100, h0 - dy)) + "px"; });
      function end() {
        if (!drag) return; drag = false; sh.classList.remove("drag");
        var h = sh.getBoundingClientRect().height, H = innerHeight;
        if (!moved) { setS(st === "min" ? "half" : "min"); return; }
        setS([["min", 64], ["half", H * 0.48], ["full", H - 100]].sort(function (a, b) { return Math.abs(a[1] - h) - Math.abs(b[1] - h); })[0][0]);
      }
      hd.addEventListener("pointerup", end); hd.addEventListener("pointercancel", end);
      document.getElementById("q").addEventListener("input", function () { if (sheetMode() && this.value.trim().length >= 2) setS("half"); });
    })();
    (function () {
      var sh = document.getElementById("psheet"), hd = document.getElementById("phead"); if (!sh || !hd) return;
      var st = "min", sy = 0, h0 = 0, moved = false, drag = false;
      function setS(s) { st = s; sh.classList.remove("p-min", "p-half", "p-full"); sh.classList.add("p-" + s); sh.style.height = ""; }
      P.set = setS; P.toggle = function () { setS(st === "min" ? "half" : "min"); };
      panel.addEventListener("click", function (ev) { if (ev.target.closest("[data-pchev]")) { ev.stopPropagation(); P.toggle(); } }, true);
      document.getElementById("pbk").addEventListener("click", function () { el.back.click(); });
      document.getElementById("prow").addEventListener("click", function (e) { if (!e.target.closest(".pclose")) return; e.stopPropagation(); if (state.sel) clearSel(); else el.back.click(); });
      hd.addEventListener("pointerdown", function (e) { if (e.target.closest("button")) return; drag = true; moved = false; sy = e.clientY; h0 = sh.getBoundingClientRect().height; sh.classList.add("drag"); try { hd.setPointerCapture(e.pointerId); } catch (x) {} });
      hd.addEventListener("pointermove", function (e) { if (!drag) return; var dy = e.clientY - sy; if (Math.abs(dy) > 4) moved = true; sh.style.height = Math.max(64, Math.min(innerHeight - 90, h0 - dy)) + "px"; });
      function end() {
        if (!drag) return; drag = false; sh.classList.remove("drag");
        var h = sh.getBoundingClientRect().height, H = innerHeight;
        if (!moved) { setS(st === "min" ? "half" : "min"); return; }
        setS([["min", 64], ["half", H * 0.46], ["full", H - 90]].sort(function (a, b) { return Math.abs(a[1] - h) - Math.abs(b[1] - h); })[0][0]);
      }
      hd.addEventListener("pointerup", end); hd.addEventListener("pointercancel", end);
    })();
    document.getElementById("zin").addEventListener("click", function () { m.zoomIn(); });
    document.getElementById("zout").addEventListener("click", function () { m.zoomOut(); });
    document.getElementById("zhome").addEventListener("click", function () { view.focus = null; showTies(null); document.getElementById("peek").hidden = true; spanHi(null); go("world"); });
    document.getElementById("mapctl").addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      if (b.id === "tilt") setTilt(!M.tilt); else if (b.getAttribute("data-mode") !== M.mode) setMode(b.getAttribute("data-mode"));
    });
    if (window.matchMedia) { var mq = matchMedia("(prefers-color-scheme: dark)"); (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(function () { setTimeout(function () { setMode(M.mode); }, 60); }); }
    setTimeout(function () { var tp = document.getElementById("ztip"); if (tp) tp.classList.add("gone"); }, 6000);
    syncCtl();
  }
