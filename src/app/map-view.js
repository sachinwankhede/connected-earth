  /* ---------- Map view ---------- */
  var US = "United States of America";
  var view = { level: "world", cont: null, country: null, state: null };
  var M = window.__M = { P: {} };
  var CONT_BOX = { "Africa": [-20, -36, 52, 38], "Asia": [26, -11, 180, 78], "Europe": [-25, 34, 45, 72], "North America": [-170, 7, -52, 75], "South America": [-82, -56, -34, 13], "Oceania": [110, -48, 180, 0], "Antarctica": [-180, -90, 180, -62] };
  var COUNTRY_BOX = {}; COUNTRY_BOX[US] = [-125, 24, -66.5, 49.5]; COUNTRY_BOX["Canada"] = [-141, 41, -52, 83];
  var SHORTNAME = {}; SHORTNAME[US] = "United States";
  function nm(s) { return SHORTNAME[s] || s; }
  var KC = { "Forest": "#2f7d4f", "Grassland": "#b8902c", "Desert": "#d0702f", "Lakes & wetlands": "#3b6fd0", "Coast & ocean": "#139aa3", "Polar & mountain": "#8a6fc0", "Urban": "#c0457a" };
  var KC_BASE = Object.assign({}, KC);
  // brighter set for the dark satellite imagery; chips and map dots always use the same set
  var KC_SAT = { "Forest": "#43c779", "Grassland": "#f0c040", "Desert": "#ff8f4a", "Lakes & wetlands": "#5f95ff", "Coast & ocean": "#2fd4de", "Polar & mountain": "#b79cff", "Urban": "#ff6fa8" };
  var FL = { q: "", kind: null, park: false, local: false, hits: null };   /* hits: ids the word index (or a species' places file) found for q; until then the card text decides */
  function qWords() { if (FL.wq !== FL.q) { FL.wq = FL.q; FL.w = srchWords(FL.q); } return FL.w; }   /* the typed words, split once per text */
  function jHit(c) { return !c.li || qWords().every(function (w) { return c.li.textContent.toLowerCase().indexOf(w) >= 0; }); }   /* a journey card holds every typed word (#443) */
  function pass(e) {
    if (FL.kind && kindsOf(FL.kind).indexOf(e.kind) < 0) return false;
    if (FL.park && !e.park) return false;
    if (e.level === "local" && !FL.local && !FL.q) return false;
    if (FL.q && M.chip === FL.q) return FL.hits ? FL.hits.has(e.id) : (e._n || (e._n = srchWords(e.name + " " + e.place).join(" "))).indexOf(FL.q) >= 0;   /* a species filter: the places of that species */
    if (FL.q) {   /* a search: the name or the region contains every typed word (#480); the species and stories of a place do not count here, the Species tab has them */
      if (!e._n) e._n = srchWords(e.name + " " + e.place).join(" ");
      return qWords().every(function (w) { return e._n.indexOf(w) >= 0; });
    }
    return true;
  }
  function inRegion(e) {
    if (!pass(e)) return false;
    if (view.level === "world") return true;
    if (view.level === "continent") return e.conts.indexOf(view.cont) >= 0;
    if (view.level === "country") return e.countries.indexOf(view.country) >= 0;
    return (e.states || []).indexOf(view.state) >= 0;
  }
  function ecoEnds(c) { return (c.type === "species" ? c.ends : [c.from, c.to]).filter(Boolean); }
  function lonlatBox(b) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (var i = 0; i <= 8; i++) for (var j = 0; j <= 8; j++) {
      var p = M.proj([b[0] + (b[2] - b[0]) * i / 8, b[1] + (b[3] - b[1]) * j / 8]);
      x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]);
    }
    return [x0, y0, x1, y1];
  }
  function tieOn(id) {
    var on = {}; if (!id) return on; on[id] = 1;
    tiesFor(id).filter(function (t) { return inRegion(ECO_BY[t.eco]); }).slice(0, 8).forEach(function (t) { on[t.eco] = 1; });
    CROSS.forEach(function (c) {
      var ends = ecoEnds(c).map(function (en) { return en.eco; });
      if (ends.indexOf(id) >= 0) ends.forEach(function (o) { on[o] = 1; });
    });
    return on;
  }
  M.go = function (l, a) { go(l, a); };
  function go(level, a) {
    /* moving to another region closes any open place card and its highlighted links */
    view.focus = null; M.tieId = null; M.peekId = null; var pk0 = document.getElementById("peek"); if (pk0) pk0.hidden = true; spanHi(null);
    if (level === "world") view = { level: "world", cont: null, country: null, state: null };
    else if (level === "continent") view = { level: "continent", cont: a, country: null, state: null };
    else if (level === "country") { view = { level: "country", cont: M.countryBy[a].cont, country: a, state: null }; if (a === US) ensureStates(); }
    else { view = { level: "state", cont: "North America", country: US, state: a }; ensureStates(); }
    renderView(true);
  }
  function crumbHTML() {
    var parts = [{ t: "World", l: "world" }];
    if (view.cont) parts.push({ t: view.cont, l: "continent", a: view.cont });
    if (view.country) parts.push({ t: nm(view.country), l: "country", a: view.country });
    if (view.state) parts.push({ t: view.state, l: "state", a: view.state });
    return parts.map(function (p, i) {
      var last = i === parts.length - 1;
      return (i ? '<span class="sep" aria-hidden="true">›</span>' : "") +
        (last ? '<span aria-current="page">' + p.t + "</span>" : '<button type="button" data-go="' + p.l + '" data-a="' + (p.a || "").replace(/"/g, "&quot;") + '">' + p.t + "</button>");
    }).join("");
  }
  /* Chip counts (#261). The build writes the number of places per region, kind and park (api/places/<main|pilot>/counts.json, as [world places, local places]); the chips read it once
     it has arrived (fetched at the first touch, so the first view makes no extra request) and count the places in memory until then, and whenever the file cannot answer: a search text, a kind and parks together, or the local
     button on before the local places are in. M.countsCheck lists the chips where the two answers differ (tests). */
  var CNT = null;
  function loadCounts() { if (CNT || M.countsP) return M.countsP; M.countsP = Data.counts().then(function (c) { CNT = c; return c; }).catch(function () { M.countsP = null; return null; }); return M.countsP; }
  M.loadCounts = loadCounts;
  function scanCount(lvl, k) { return ECOS.filter(pass).filter(function (e) { return lvl === "continent" ? e.conts.indexOf(k) >= 0 : lvl === "country" ? e.countries.indexOf(k) >= 0 : (e.states || []).indexOf(k) >= 0; }).length; }
  function fileCount(lvl, k) {
    if (!CNT || FL.q || (FL.kind && FL.park) || (FL.local && !Places.done)) return null;
    var r = CNT.regions[(lvl === "continent" ? "c:" : lvl === "country" ? "k:" : "s:") + k]; if (!r) return null;
    var n = 0;
    if (FL.kind) { kindsOf(FL.kind).forEach(function (kd) { var x = r.k[kd]; if (x) n += x[0] + (FL.local ? x[1] : 0); }); return n; }
    if (FL.park) return r.p[0] + (FL.local ? r.p[1] : 0);
    return r.n[0] + (FL.local ? r.n[1] : 0);
  }
  M.countsCheck = function () {
    var bad = [], seen = {}; if (!CNT) return null;
    ECOS.forEach(function (e) {
      [["continent", e.conts], ["country", e.countries], ["state", e.states || []]].forEach(function (g) {
        g[1].forEach(function (k) {
          var id = g[0] + ":" + k; if (seen[id]) return; seen[id] = 1;
          var f = fileCount(g[0], k), c = scanCount(g[0], k);
          if (f !== null && f !== c) bad.push({ lvl: g[0], k: k, file: f, scan: c });
        });
      });
    });
    return bad;
  };
  /* Chips (#261): the regions one level below the view that hold a place passing the filters, from the counts file or else from memory. */
  function scanKeys(lvl) {
    var keys = [];
    if (lvl === "continent") ECOS.filter(pass).forEach(function (e) { e.conts.forEach(function (c) { if (keys.indexOf(c) < 0) keys.push(c); }); });
    else if (lvl === "country") ECOS.filter(inRegion).forEach(function (e) { e.countries.forEach(function (c) { if (keys.indexOf(c) < 0 && M.countryBy[c] && M.countryBy[c].cont === view.cont) keys.push(c); }); });
    else ECOS.filter(inRegion).forEach(function (e) { (e.states || []).forEach(function (s) { if (keys.indexOf(s) < 0) keys.push(s); }); });
    return keys;
  }
  function fileKeys(lvl) {
    if (!CNT) return null;
    var pre = lvl === "continent" ? "c:" : lvl === "country" ? "k:" : "s:", keys = [], answered = true;
    Object.keys(CNT.regions).forEach(function (r) {
      if (r.indexOf(pre) !== 0) return;
      var k = r.slice(2);
      if (lvl === "country" && !(M.countryBy[k] && M.countryBy[k].cont === view.cont)) return;
      var n = fileCount(lvl, k); if (n === null) { answered = false; return; }
      if (n > 0) keys.push(k);
    });
    return answered ? keys : null;
  }
  function chipKeys(lvl) { return fileKeys(lvl) || scanKeys(lvl); }
  M.listsCheck = function () {   /* tests: the chips of the current view from the file and from the places in memory */
    var lvl = view.level === "world" ? "continent" : view.level === "continent" ? "country" : view.level === "country" && view.country === US ? "state" : null;
    var f = lvl && fileKeys(lvl); if (!f) return null;
    var a = f.slice().sort().join("|"), b = scanKeys(lvl).sort().join("|");
    return a === b ? [] : [{ lvl: lvl, file: a, scan: b }];
  };
  function chipsHTML() {
    var keys = [], lvl, lab;
    if (M.tab === "species") return "";   /* the Species tab fills this row with its groups */
    if (M.tab === "journeys") {
      var jk = [];
      CROSS.forEach(function (c) { ecoEnds(c).forEach(function (en) { ECO_BY[en.eco].conts.forEach(function (k) { if (jk.indexOf(k) < 0) jk.push(k); }); }); });
      var jn = function (k) { return CROSS.filter(function (c) { return jHit(c) && ecoEnds(c).some(function (en) { return ECO_BY[en.eco].conts.indexOf(k) >= 0; }); }).length; };   /* the counts follow the search (#495) */
      if (FL.q) jk = jk.filter(jn);
      if (FL.q && !jk.length) return "";
      jk.sort(function (a, b) { return jn(b) - jn(a) || (a < b ? -1 : 1); });
      return '<span class="lbl">Continent</span>' + [""].concat(jk).map(function (k) { return '<button type="button" class="chip' + ((M.jcont || "") === k ? " on" : "") + '" data-jc="' + k.replace(/"/g, "&quot;") + '">' + (k ? nm(k) + " <b>" + jn(k) + "</b>" : "All") + "</button>"; }).join("");
    }
    if (view.level === "world") { lvl = "continent"; lab = "Browse by continent"; }
    else if (view.level === "continent") { lvl = "country"; lab = "Countries"; }
    else if (view.level === "country" && view.country === US) { lvl = "state"; lab = "States"; }
    else return "";
    keys = chipKeys(lvl);
    while (keys.length === 1 && FL.q && lvl !== "state") {   /* a search that sits in one region: the pills go one level down (#528) */
      var sv = view, k2;
      if (lvl === "continent") view = { level: "continent", cont: keys[0], country: null, state: null }; else if (keys[0] === US) view = { level: "country", cont: view.cont, country: US, state: null }; else break;
      k2 = scanKeys(lvl === "continent" ? "country" : "state"); view = sv;
      if (!k2.length) break;
      lvl = lvl === "continent" ? "country" : "state"; lab = lvl === "country" ? "Countries" : "States"; keys = k2;
    }
    if (keys.length < 2) return "";
    keys.sort();
    function count(k) { var f = fileCount(lvl, k); return f !== null ? f : scanCount(lvl, k); }
    keys.sort(function (a, b) { return count(b) - count(a) || (nm(a) < nm(b) ? -1 : 1); });
    return '<span class="lbl">' + lab + "</span>" + keys.map(function (k) {
      return '<button type="button" class="chip" data-go="' + lvl + '" data-a="' + k.replace(/"/g, "&quot;") + '">' + nm(k) + " <b>" + count(k) + "</b>" + "</button>";
    }).join("");
  }
  function spanText(e) {
    var p = [];
    if (e.countries.length > 1) p.push(e.countries.map(nm).join(" · "));
    if ((e.states || []).length > 1) p.push(e.states.join(" · "));
    return p.length ? "Spans " + p.join(" — ") : "";
  }
  function dimChips() {
    var m = M.map, box = document.getElementById("kinds"); if (!box) return;
    var bd = (m && M.styleReady && m.getBounds) ? m.getBounds() : null, sk = FL.kind; FL.kind = null;
    var vis = bd ? ECOS.filter(function (e) { return inRegion(e) && (!e.auto || e.level === "local" || M.hiZ || FL.q || view.level !== "world") && bd.contains([e.lon, e.lat]); }) : null;
    FL.kind = sk;
    Array.prototype.forEach.call(box.querySelectorAll("[data-kind]"), function (b) {
      var lab = b.getAttribute("data-kind"), ks = kindsOf(lab);
      var has = !vis || lab === FL.kind || vis.some(function (e) { return ks.indexOf(e.kind) >= 0; });
      b.classList.toggle("dim", !has);
    });
  }
  var KGROUPS = [["Forest", ["Forest"]], ["Grass & desert", ["Grassland", "Desert"]], ["Freshwater", ["Lakes & wetlands"]], ["Ocean", ["Coast & ocean"]], ["Cold & high", ["Polar & mountain"]], ["Urban", ["Urban"]]];
  function kindsOf(label) { for (var i = 0; i < KGROUPS.length; i++) if (KGROUPS[i][0] === label) return KGROUPS[i][1]; return [label]; }
  function kindsHTML() {
    var nl = Places.nLocal, lb = document.getElementById("locbtn");
    if (lb) { lb.style.display = nl ? "" : "none"; lb.setAttribute("aria-pressed", FL.local ? "true" : "false"); }
    document.getElementById("kinds").innerHTML = KGROUPS.map(function (g) {
      var n = ECOS.filter(function (e) { return g[1].indexOf(e.kind) >= 0 && (FL.local || e.level !== "local"); }).length;
      if (!n || (g[0] === "Urban" && n < 5)) return "";
      return '<button type="button" class="chip' + (FL.kind === g[0] ? " on" : "") + '" data-kind="' + g[0] + '" aria-pressed="' + (FL.kind === g[0]) + '"><i class="kd" style="--kc:' + KC[g[1][0]] + '"></i>' + g[0] + "</button>";
    }).join(""); dimChips(); kfade();
  }
  function kfade() { ["kinds", "regions"].forEach(function (id) { var k = document.getElementById(id); if (k) k.classList.toggle("fade", k.scrollWidth - k.scrollLeft - k.clientWidth > 4); }); }
  addEventListener("resize", function () { kfade(); });
  document.addEventListener("scroll", function (ev) { if (ev.target && (ev.target.id === "kinds" || ev.target.id === "regions")) kfade(); }, true);
  function tiesHTML(id) {
    var out = [], x = [];
    CROSS.forEach(function (c) { var ends = ecoEnds(c); if (ends.some(function (en) { return en.eco === id; })) x.push(c.title); });
    var t = tiesFor(id).slice(0, 5);
    if (x.length) out.push("<b>Linked by</b>" + x.join(" · "));
    if (t.length) out.push("<b>Shares species with</b>" + t.map(function (q) {
      var o = ECO_BY[q.eco]; return '<button type="button" data-peek="' + q.eco + '">' + o.short + '</button>' + (q.spp ? ' <span class="sp">(' + q.spp.slice(0, 3).join(", ").toLowerCase() + (q.n > 3 ? " +" + (q.n - 3) : "") + ")</span>" : "");
    }).join(" · "));
    return out.length ? '<div class="ties">' + out.join("<br>") + "</div>" : "";
  }
  function fillPeekTies(id) {   /* the ties file came after the card was drawn: put the line in */
    var pe = document.getElementById("peek"); if (!pe || pe.hidden || M.peekId !== id) return;
    var h = tiesHTML(id), t = pe.querySelector(".ties"), b = pe.querySelector(".pbtns");
    if (t) t.outerHTML = h; else if (h && b) b.insertAdjacentHTML("beforebegin", h);
  }
  var ICON_SHARE = '<button type="button" class="ibtn" data-share="1" aria-label="Share link" title="Share"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg><svg class="ok" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 13l4 4L19 7"/></svg></button>';
  var ICON_CLOSE = '<button type="button" class="ibtn" data-closepeek="1" aria-label="Close card" title="Close"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>';
  M.peek = function (id) { peek(id); };
  /* a place that is not loaded yet (a local one, before the local places have come): fetch them, then do it again */
  function notYet(id, again) { if (ECO_BY[id] || Places.done) return false; Places.loadLocals().then(function (ok) { if (ok) again(); }); return true; }
  function peek(id) {
    if (notYet(id, function () { peek(id); })) return;
    var e = ECO_BY[id], pe = document.getElementById("peek"), ci = cimg(id);
    pe.innerHTML = '<div class="pimg">' + (ci ? ci.innerHTML : "") + '</div><div class="pbody"><div class="pact">' + ICON_SHARE + ICON_CLOSE + '</div><span class="where">' + e.place + '</span><h2>' + e.name + '</h2><p>' + e.blurb + '</p>' + (spanText(e) ? '<p class="spans">' + spanText(e) + "</p>" : "") + tiesHTML(id) + '<div class="pbtns"><button type="button" class="btn go" data-open="' + id + '"><span class="long">Open the food web</span><span class="short">Open</span> &rarr;</button></div></div>';
    pe.hidden = false; M.peekId = id; spanHi(e); showTies(id); parkHi(id);
    /* the card floats over the map, so the page never needs to scroll */
  }

