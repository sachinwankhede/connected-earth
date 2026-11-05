  /* a place's list card is built the first time it is needed (shown in the list, or its picture is used elsewhere), not for every place at startup */
  function addEcoOption(e) {
    if (!el.eco) return;
    var o = document.createElement("option");
    o.value = e.id; o.textContent = e.name;
    el.eco.appendChild(o);
  }
  function makeCard(e) {
    if (e.li) return e.li;
    var sp = e.idx.ns, li = document.createElement("li");
    li.innerHTML = '<button type="button" class="card" data-eco="' + e.id + '"><div class="cimg" id="ci-' + e.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[e.icon] || "") + '</svg></div><span class="where">' + e.place + "</span>" + (spanText(e) ? '<span class="span">Spans ' + (e.countries.length > 1 ? e.countries.length + " countries" : e.states.length + " states") + "</span>" : "") + "<h2>" + e.name + "</h2><p>" + e.blurb + '</p><span class="where">' + sp + " species \u00b7 " + e.idx.nr + ' feeding links' + '</span><span class="go">Open the food web &rarr;</span></button>';
    e.li = li; if (M.wantPhoto) M.wantPhoto(e); else ecoPhoto(e);
    return li;
  }
  /* the search text changed (typing, or an address that carries s=): box, filter, list and map follow (#412) */
  function runSearch(text) {
    clearTimeout(M.qT);
    var q = document.getElementById("q"); if (q.value !== text) q.value = text; qSync();
    FL.q = text.trim().toLowerCase(); if (FL.q && M.tab === "journeys") setTab("places"); view.focus = null; document.getElementById("peek").hidden = true; showTies(null);
    searchFor(FL.q);   /* a query is drawn once, when the index has answered (#414); the old results stay until then */
    if (!FL.q) renderView(false);   /* an empty box is drawn at once */
  }
  function qSync() { var q = document.getElementById("q"), c = document.getElementById("qclr"); if (!q || !c) return; c.hidden = !q.value; document.getElementById("qwrap").classList.toggle("has", !!q.value); }   /* the Clear link shows only when there is text */
  function cimg(id) { var e = ECO_BY[id]; return e ? makeCard(e).querySelector(".cimg") : null; }
  function buildMap() {
    var xc = document.getElementById("xcards");
    CROSS.forEach(function (c) {
      var en = ecoEnds(c);
      var li = document.createElement("li"), fi = ECO_BY[en[0].eco].icon;
      li.innerHTML = '<div class="jcard" id="xc-' + c.id + '" role="button" tabindex="0"><span class="jimg" id="xi-' + c.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[fi] || "") + '</svg></span><span class="jbody"><span class="jroute">' + ECO_BY[en[0].eco].short + ' <i aria-hidden="true">\u2192</i> ' + ECO_BY[en[en.length - 1].eco].short + '</span><b class="jtitle">' + c.title + '</b></span><span class="jgo" aria-hidden="true">\u203a</span></div>';
      xc.appendChild(li); c.li = li;
    });
    xc.addEventListener("keydown", function (ev) { var d = ev.target.closest(".jcard"); if (d && ev.target === d && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); showJourney(d.id.slice(3)); } });
    xc.addEventListener("click", function (ev) {
      var d = ev.target.closest(".jcard"); if (d) showJourney(d.id.slice(3));
    });
    cards.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-eco]");
      if (b) showPlace(b.getAttribute("data-eco"));
    });
    function nav(ev) {
      var b = ev.target.closest("[data-go]");
      if (b) go(b.getAttribute("data-go"), b.getAttribute("data-a"));
    }
    document.getElementById("crumbs").addEventListener("click", nav);
    var qIn = document.getElementById("q");
    qIn.addEventListener("keydown", function (ev) { if (ev.key === "Enter") qIn.blur(); });   /* the keyboard leaves so the results show */
    document.getElementById("qclr").addEventListener("click", function (ev) { ev.preventDefault(); qIn.value = ""; qIn.dispatchEvent(new Event("input", { bubbles: true })); qIn.focus(); });
    qIn.addEventListener("input", qSync);
    document.getElementById("q").addEventListener("input", function () {
      var v = this.value, now = Date.now(); if (!FL.q && v.trim()) M.pushNext = true;
      clearTimeout(M.qT);
      if (!v.trim() || now - (M.qLast || 0) >= 120) { M.qLast = now; runSearch(v); return; }   /* the first letter and Clear answer at once; letters typed within 120 ms of the last run wait for the end of the burst (#414) */
      M.qT = setTimeout(function () { M.qLast = Date.now(); runSearch(document.getElementById("q").value); }, 120 - (now - M.qLast));
    });
    qIn.addEventListener("focus", function () { Places.loadLocals(); }, { once: true });   /* the local places a search needs start coming as soon as the box is used (#414) */
    document.getElementById("empty").addEventListener("click", function (ev) { if (ev.target.closest("#eclr")) { qIn.value = ""; qIn.dispatchEvent(new Event("input", { bubbles: true })); } });   /* the first letter adds a history entry, so Back clears the search before leaving (#412) */
    document.getElementById("locbtn").addEventListener("click", function () { FL.local = !FL.local; view.focus = null; filterView(); if (FL.local) Places.loadLocals(); });
    document.getElementById("kinds").addEventListener("click", function (ev) {
      var pk = ev.target.closest("[data-park]");
      if (pk) { FL.park = !FL.park; view.focus = null; filterView(); return; }
      var b = ev.target.closest("[data-kind]"); if (!b) return;
      FL.kind = FL.kind === b.getAttribute("data-kind") ? null : b.getAttribute("data-kind"); view.focus = null; filterView();
    });
    document.getElementById("peek").addEventListener("click", function (ev) {
      var o = ev.target.closest("[data-open]"); if (o) { showPlace(o.getAttribute("data-open")); return; }
      var pk = ev.target.closest("[data-peek]"); if (pk) { peek(pk.getAttribute("data-peek")); return; }
      if (ev.target.closest("[data-closepeek]")) { this.hidden = true; spanHi(null); showTies(null); }
    });
    document.getElementById("regions").addEventListener("click", nav);
    ECOS.forEach(addEcoOption);
    el.eco.addEventListener("change", function () { showWeb(el.eco.value); });
  }
  var NOTE = {};
  function tabCount(t, n) {   /* while a search is on every tab says how many it found: on its label and in one note line under the tabs, in the same words on all three (#443, #449) */
    Array.prototype.forEach.call(document.querySelectorAll('[data-tab="' + t + '"]'), function (b) { var s = t[0].toUpperCase() + t.slice(1) + (n == null ? "" : " " + n); if (b.textContent !== s) b.textContent = s; });   /* only when it changed: this runs on every redraw */
    var k = t === "places" ? "place" : t === "journeys" ? "journey" : "species";
    NOTE[t] = n == null ? "" : (n || "No") + " " + (n === 1 ? k + " matches" : (k === "species" ? k : k + "s") + " match") + " \u201c" + FL.q + "\u201d";
    showNote();
  }
  function showNote() { var e = document.getElementById("qnote"), s = FL.q && (FL.busy ? "Searching\u2026" : NOTE[M.tab || "places"] + (FL.limited ? " \u00b7 Search is limited right now" : "")); s = s || ""; if (e.textContent !== s) e.textContent = s; e.hidden = !s; }
  function applyJ() {
    var jw = FL.q ? srchWords(FL.q) : [];   /* a search also narrows the journeys: every typed word must be in the card (#443) */
    CROSS.forEach(function (c) { if (!c.li) return; c.li.hidden = (!!M.jcont && !ecoEnds(c).some(function (en) { return ECO_BY[en.eco].conts.indexOf(M.jcont) >= 0; })) || !jw.every(function (w) { return c.li.textContent.toLowerCase().indexOf(w) >= 0; }); });
    M.nJ = CROSS.filter(function (c) { return c.li && !c.li.hidden; }).length; tabCount("journeys", FL.q ? M.nJ : null);
    document.getElementById("xcards").hidden = !M.nJ; document.getElementById("jintro").hidden = !M.nJ; document.getElementById("jempty").hidden = M.nJ > 0;
    updCount();
  }
  function updCount() {
    var j = M.tab === "journeys", sr = document.getElementById("srow"), nj = (M.nJ || 0) + ((M.nJ || 0) === 1 ? " journey" : " journeys") ;
    if (sr && M.srHTML !== undefined) { sr.classList.toggle("jtab", j); if (j) { sr.innerHTML = '<span class="stt">Connected Earth</span>'; sr.classList.remove("home"); } else { sr.innerHTML = M.srHTML; sr.classList.toggle("home", !!M.srHome); } }
    var ji = document.getElementById("jintro"); if (ji) ji.innerHTML = "<b>" + nj + "</b>" + (M.jcont ? " in " + M.jcont : "") + ". Animals that travel, and nutrients that are carried, from one place to another.";
    if (el.webview.hidden && M.statsHTML !== undefined) { if (j) el.stats.textContent = nj + (M.jcont ? " in " + M.jcont : ""); else el.stats.innerHTML = M.statsHTML; }
  }
  /* The Species tab's code is not in the first view: it is one small file, loaded the first time the tab opens (#422) */
  var SPT = null, SPQ = [];
  function withSpeciesTab(cb) {
    if (SPT) { cb(SPT); return; }
    SPQ.push(cb); if (SPQ.length > 1) return;
    var sc = document.createElement("script"); sc.async = true; sc.src = location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "") + "species-tab-__TABVER__.js";
    sc.onload = function () { var f = (window.__chunk || {})["species-tab"]; if (!f) { SPQ = []; return; } SPT = f({ Data: Data, PhotoRegistry: PhotoRegistry, esc: esc, leaf: SUG_LEAF, chev: SUG_CHEV, find: function (q) { var ws = srchWords(q), l = ws[ws.length - 1]; return !l || l.length < 2 ? Promise.resolve(null) : sugFile(l.slice(0, 2)).then(function (d) { return sugPick(q, { s: d.s }, 40); }); }, go: function (l) { M.pushNext = true; showSpecies(sidOf({ latin: l }), "Species"); },
      P: { FL, M, PV, ICONS, PNAMES, ABOUT, ECO_BY, PHOTOS, escH, shareBtn, aboutText, footHTML, creditHTML, fillPhotos, photoOf, bindPhoto, sppPlaces, speciesMap, showPlace, closeSpecies, makeCard, pWant } }); var q = SPQ; SPQ = []; q.forEach(function (f2) { f2(SPT); }); };
    sc.onerror = function () { SPQ = []; var st = document.getElementById("sptab"); if (st) st.innerHTML = '<p class="fine">The species could not be loaded. Check your connection and try again.</p>'; };
    document.head.appendChild(sc);
  }
  function setTab(t) {
    M.tab = t; showNote();
    if (t === "journeys") withSpeciesPhotos(loadJourneyPhotos);
    var rg = document.getElementById("regions"); if (rg) { rg.innerHTML = chipsHTML(); kfade(); }
    var sb = document.getElementById("sbody"); if (sb) { sb.classList.toggle("tab-j", t === "journeys"); sb.classList.toggle("tab-s", t === "species"); }
    var st = document.getElementById("sptab"); if (st) st.hidden = t !== "species";
    if (t === "species") withSpeciesTab(function (c) { c.open(); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-tab]"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-tab") === t ? "true" : "false"); });
    applyJ();
    if (sb && sb.scrollTo) sb.scrollTo(0, 0);
  }
  (function () {
    var sh = document.getElementById("sheet"), sb = document.getElementById("sbody");
    var fadeFrame = null;
    function fade() {
      if (fadeFrame !== null) return;
      fadeFrame = requestAnimationFrame(function () {
        fadeFrame = null;
        if (sh && sb) sh.classList.toggle("atend", sb.scrollTop + sb.clientHeight >= sb.scrollHeight - 8);
      });
    }
    if (sb) { sb.addEventListener("scroll", fade, { passive: true }); new MutationObserver(fade).observe(sb, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "class"] }); }
    if (sh) new MutationObserver(fade).observe(sh, { attributes: true, attributeFilter: ["class", "style"] });
    addEventListener("resize", fade); setTimeout(fade, 300);
  })();
  (function () { var rg = document.getElementById("regions"); if (rg) rg.addEventListener("click", function (ev) { var b = ev.target.closest("[data-jc]"); if (!b) return; M.jcont = b.getAttribute("data-jc") || null; rg.innerHTML = chipsHTML(); kfade(); applyJ(); }); })();
  document.addEventListener("click", function (ev) { var b = ev.target.closest("[data-tab]"); if (b) { setTab(b.getAttribute("data-tab")); if (M.setSheet && M.sheetState === "min") M.setSheet("half"); } });
  function hlCard(id) {
    var c = document.getElementById("xc-" + id);
    if (!c) return;
    if (c.parentNode && c.parentNode.hidden) M.jcont = null;
    setTab("journeys");
    c.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
    c.classList.add("hl");
    setTimeout(function () { c.classList.remove("hl"); }, 1600);
  }
  M.hlCard = hlCard; M.showTies = function (id) { showTies(id); };
  M.showJourney = function (id) { showJourney(id); }; M.showPlace = function (id) { showPlace(id); }; M.ecoIds = function () { return ECOS.map(function (e) { return e.id; }); };
  M.journeyIds = function () { return CROSS.map(function (c) { return c.id; }); };
