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
    document.getElementById("q").addEventListener("input", function () { FL.q = this.value.trim().toLowerCase(); searchFor(FL.q); if (FL.q && M.tab === "journeys") setTab("places"); view.focus = null; document.getElementById("peek").hidden = true; showTies(null); renderView(FL.q.length >= 3); });
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
  function applyJ() {
    CROSS.forEach(function (c) { if (!c.li) return; c.li.hidden = !!M.jcont && !ecoEnds(c).some(function (en) { return ECO_BY[en.eco].conts.indexOf(M.jcont) >= 0; }); });
    M.nJ = CROSS.filter(function (c) { return c.li && !c.li.hidden; }).length;
    document.getElementById("xcards").hidden = !M.nJ; document.getElementById("jintro").hidden = !M.nJ; document.getElementById("jempty").hidden = M.nJ > 0;
    updCount();
  }
  function updCount() {
    var j = M.tab === "journeys", sr = document.getElementById("srow"), nj = (M.nJ || 0) + ((M.nJ || 0) === 1 ? " journey" : " journeys");
    if (sr && M.srHTML !== undefined) { sr.classList.toggle("jtab", j); if (j) { sr.innerHTML = '<span class="stt">Connected Earth</span>'; sr.classList.remove("home"); } else { sr.innerHTML = M.srHTML; sr.classList.toggle("home", !!M.srHome); } }
    var ji = document.getElementById("jintro"); if (ji) ji.innerHTML = "<b>" + nj + "</b>" + (M.jcont ? " in " + M.jcont : "") + ". Animals that travel, and nutrients that are carried, from one place to another.";
    if (el.webview.hidden && M.statsHTML !== undefined) { if (j) el.stats.textContent = nj + (M.jcont ? " in " + M.jcont : ""); else el.stats.innerHTML = M.statsHTML; }
  }
  function setTab(t) {
    M.tab = t;
    if (t === "journeys") withSpeciesPhotos(loadJourneyPhotos);
    var rg = document.getElementById("regions"); if (rg) { rg.innerHTML = chipsHTML(); kfade(); }
    var sb = document.getElementById("sbody"); if (sb) sb.classList.toggle("tab-j", t === "journeys");
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
