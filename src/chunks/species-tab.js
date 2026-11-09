/* The Species tab (#422). This code is not in the page: the page loads this file the first time the tab opens (withSpeciesTab in src/app/cards.js) and gives it what it
   needs in A (Data, the photo registry, escaping, the row icons, and go(latin) which opens a species page). It reads api/species-tab/ only through A.Data.
   First screen: the species found in the most places, then the groups; a group opens its own list, 250 rows at a time. */
window.__chunk = window.__chunk || {};
window.__chunk["species-tab"] = function (A) {
  var box = document.getElementById("sptab"), started = false, top = [], groups = [];
  var mmCSS = [
      ".sheet.mm .srow > * { display: none; }",
      ".sheet.mm .srow { min-height: 0; height: 0; margin: 0; overflow: hidden; }",
      ".sheet.mm .srow::after { display: none; }",
      ".sheet.mm .shead { padding-bottom: 0; }",
      ".sheet.mm .sbody { padding-top: 0; }",
      ".sheet.mm .qhead { position: relative; padding-right: 48px; min-height: 44px; display: flex; flex-wrap: wrap; align-items: center; gap: 0 4px; margin: 0 0 2px; }",
      ".qhead .qx { position: absolute; right: 0; top: 0; width: 44px; height: 44px; border: 0; background: transparent; color: var(--muted); font-size: 18px; cursor: pointer; }",
      ".qtrail { display: none; align-items: center; flex-wrap: wrap; gap: 0 4px; margin: 0 0 8px; padding: 0 2px; font-size: 13px; font-weight: 600; }",
      ".sheet.mm .qtrail:not([hidden]) { display: flex; }",
      ".qtrail .sep { color: var(--muted); }",
      ".qtrail .sbk { border: 0; background: transparent; color: var(--accent); font: inherit; padding: 6px 4px; min-height: 32px; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }",
      ".qtrail .cur { padding: 6px 4px; }",
      "body:has(.sheet.mm) .crumbs { display: none; }"].join("\n");   /* map-mode layout (owner, 9 Nov): title row with a close at its right, then the region trail, then the pills; kept here so the first view does not carry it */
  function mmStyle() { if (document.getElementById("mmcss")) return; var st = document.createElement("style"); st.id = "mmcss"; st.textContent = mmCSS; document.head.appendChild(st); }
  function el(html, cls) { var d = document.createElement("div"); d.className = cls; d.innerHTML = html; return d; }
  function row(r) {   /* [Latin name, usual name, places, picture file or 0] */
    var c = r[3] && A.PhotoRegistry.speciesCandidate([r[3], r[0]], r[0], 1, null);
    var d = el('<span class="sgi">' + (c ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + A.esc(c.assetUrl) + '">' : A.leaf) + '</span><span class="sgt"><b></b><i></i></span>' + A.chev, "sgr");
    d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-latin", r[0]);
    d.querySelector("b").textContent = r[1]; d.querySelector("i").textContent = "Species · in " + r[2] + (r[2] === 1 ? " place" : " places");
    var im = d.querySelector("img"); if (im) im.onerror = function () { d.querySelector(".sgi").innerHTML = A.leaf; };
    return d;
  }
  function card(r) {   /* the same photo card as the place page's photo rows (.prow / .pmc): [Latin name, usual name, places, picture file or 0] */
    var c = r[3] && A.PhotoRegistry.speciesCandidate([r[3], r[0]], r[0], 1, null);
    var d = document.createElement("button"); d.className = "pmc";
    d.innerHTML = '<span class="pbox"><span class="pph' + (c ? " has" : "") + '">' + (c ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + A.esc(c.assetUrl) + '">' : A.leaf) + '</span></span><b></b><small></small>';
    d.type = "button"; d.setAttribute("data-latin", r[0]); d.querySelector("b").textContent = r[1]; d.querySelector("small").textContent = "in " + r[2] + (r[2] === 1 ? " place" : " places");
    var im = d.querySelector("img"); if (im) im.onerror = function () { var p = d.querySelector(".pph"); p.classList.remove("has"); p.innerHTML = A.leaf; };
    return d;
  }
  function strip(items) { var l = el("", "prow"); items.forEach(function (x) { l.appendChild(card(x)); }); return l; }   /* sideways, like every photo row (#484) */
  var rg = document.getElementById("regions"), ords = {}, cur = "", gen = 0;   /* ords: group key -> its orders [key, name, species, pages] (#519 level 2) */
  function chip(attr, key, on, text, n) { return '<button type="button" class="chip' + (on ? " on" : "") + '" ' + attr + '="' + key + '">' + escH(text) + (n == null ? "" : " <b>" + n + "</b>") + "</button>"; }
  function pills(on, g, ok) {   /* one row of pills, like the continents on Places: the groups; inside a group that has orders, its orders with a way back up (#519) */
    if (g && ords[g[0]]) { rg.innerHTML = '<span class="lbl">Orders</span>' + chip("data-spu", "1", false, "\u2039 Groups") + chip("data-spg", g[0], !ok, "All " + g[1], g[2]) + ords[g[0]].map(function (o) { return chip("data-spo", o[0], o[0] === ok, o[1], o[2]); }).join(""); return; }
    rg.innerHTML = '<span class="lbl">Browse by group</span>' + chip("data-spg", "", !on, "All", groups.reduce(function (n, g) { return n + g[2]; }, 0)) + groups.map(function (g) { return chip("data-spg", g[0], g[0] === on, g[1], g[2]); }).join("");
  }
  rg.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-spg],[data-spo],[data-spu]"); if (!b || box.hidden) return;
    if (b.hasAttribute("data-spu")) home(); else if (b.hasAttribute("data-spo")) openGroup(cur, b.getAttribute("data-spo")); else if (b.getAttribute("data-spg")) openGroup(b.getAttribute("data-spg")); else home();
  });
  function list(items, make) { var l = el("", "sgl"); items.forEach(function (x) { l.appendChild(make(x)); }); return l; }
  function home() {
    cur = ""; gen++; pills(""); box.innerHTML = "<h3>Found in the most places</h3>"; box.appendChild(list(top, row));
  }
  function group(g, ok) {   /* one group, or one order of it: its first page, and "Show more" for the next */
    var page = 0, shown = 0, my = ++gen, o = ok && (ords[g[0]] || []).filter(function (x) { return x[0] === ok; })[0], total = o ? o[2] : g[2], pre = "g-" + g[0] + "-" + (o ? o[0] + "-" : "");
    cur = g[0];
    if (g[4] && !ords[g[0]]) { rg.innerHTML = ""; box.innerHTML = "<h3></h3>"; box.firstChild.textContent = g[1] + " \u00b7 " + g[2];   /* the orders come first, then the row is drawn once; the old list is gone at once */
      A.Data.speciesTab("o-" + g[0] + ".json").then(function (r) { ords[g[0]] = r; if (my === gen) group(g, ok); }).catch(function () { ords[g[0]] = []; if (my === gen) group(g); }); return; }
    pills(g[0], g, ok); box.innerHTML = "<h3></h3>";
    box.querySelector("h3").textContent = g[1] + (o ? " \u203a " + o[1] : "") + " \u00b7 " + total;
    var l = el("", "sgl"), p = el('<a href="#" data-more="1"></a>', "fine"); box.appendChild(l); box.appendChild(p); p.hidden = true;
    function more() {
      var k = page++;
      A.Data.speciesTab(pre + k + ".json").then(function (rows) {
        if (my !== gen) return;
        rows.forEach(function (r) { l.appendChild(row(r)); }); shown += rows.length;
        p.hidden = shown >= total; p.firstChild.textContent = "Show " + Math.min(total - shown, 250) + " more \u203a";
      }).catch(function () { page = k; p.hidden = false; p.firstChild.textContent = "Could not load. Try again"; });
    }
    p.addEventListener("click", function (ev) { ev.preventDefault(); more(); });
    more();
  }
  var want = null;
  function openGroup(key, ok) { var g = groups.filter(function (x) { return x[0] === key; })[0]; if (g) group(g, ok); else want = key; }   /* before the groups have loaded, open() does it */
  function act(t) {
    var d = t.closest(".sgr");
    if (d && d.hasAttribute("data-latin")) A.go(d.getAttribute("data-latin"));
  }
  var qIn = document.getElementById("q"), qT, qN = 0, shown = "";
  function find() {   /* the search box on this tab looks for species only (#422 step 4) */
    var q = qIn.value.trim(), n = ++qN; if (box.hidden || !started || q === shown) return; shown = q;
    if (q.length < 2) { home(); return; }
    A.find(q).then(function (rows) {
      if (n !== qN || !rows) return;
      rg.innerHTML = ""; box.innerHTML = "";   /* what was found is said in the note under the tabs, the same on all three (#449) */
      if (rows.length) box.appendChild(list(rows, function (r) { return row([r.latin, r.name, r.n, r.pic || 0]); })); else box.insertAdjacentHTML("beforeend", '<p class="fine"><a href="#" data-clr="1">Clear</a></p>');
    }).catch(function () { if (n === qN) shown = ""; });
  }
  qIn.addEventListener("input", function () { clearTimeout(qT); qT = setTimeout(find, 150); });
  document.getElementById("qclr").addEventListener("click", function () { setTimeout(function () { shown = null; find(); }, 0); });
  box.addEventListener("click", function (ev) { if (ev.target.closest("[data-clr]")) { ev.preventDefault(); document.getElementById("qclr").click(); return; } act(ev.target); });
  box.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); act(ev.target); } });
  /* ---- the species page (#420, #445): built here, not in the first view. show(sid) runs after the first view has done the address and hidden the other views ---- */
  var P = A.P, PV = P.PV, M = P.M, escH = P.escH;
  function show(sid) {
    var words = sid.replace(/-/g, " ").replace(/^./, function (c) { return c.toUpperCase(); });
    var GL = {};   /* group key -> label, from the Species tab's groups file */
    function taxLine(d) {   /* group (a link to its list), order and family (#446) */
      if (!d.g || !GL[d.g]) return "";
      return '<p class="fine tax"><a href="#" data-sg="' + d.g + '">' + escH(GL[d.g]) + "</a>" + (d.od ? " \u203a " + escH(d.od) : "") + (d.fa ? " \u203a " + escH(d.fa) : "") + "</p>";
    }
    function page(d) {
      var latin = d.l || words, name = d.n || latin;
      return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">\u2039 ' + escH(M.spFrom || (P.FL.q ? "Search" : "Places")) + "</button>" + P.shareBtn() + "</div>" +
        '<div class="jhero"><span class="jhimg" id="sp-img">' + (P.ICONS[d.ic] ? '<svg viewBox="0 0 24 24" aria-hidden="true">' + P.ICONS[d.ic] + "</svg>" : A.leaf) + '</span><div><p class="jkind">' + escH(P.PNAMES[d.tl] || "Species") + "</p><h2>" + escH(name) + '</h2><p class="jr"><i>' + escH(latin) + "</i></p>" + taxLine(d) + "</div></div>" +
        (d.t ? '<p class="about">' + P.aboutText({ latin: latin, wiki: d.ph && d.ph[1] }) + "</p>" : "") +
        P.footHTML({ photoId: "spcredit", sources: [{ title: "Wikipedia: " + escH(latin), url: "https://en.wikipedia.org/wiki/" + encodeURIComponent(((d.ph && d.ph[1]) || latin).replace(/ /g, "_")) }] }) + "</article>";
    }
    if (M.sid !== sid) return;
    PV.innerHTML = page({});
    Promise.all([A.Data.species(sid).catch(function () { return null; }), A.Data.speciesTab("groups.json").catch(function () { return []; })]).then(function (r) {
      var d = r[0]; r[1].forEach(function (g) { GL[g[0]] = g[1]; });
      if (M.sid !== sid) return;
      d = d || {}; if (d.t) P.ABOUT[sid] = d.t;
      PV.innerHTML = page(d);
      var c = d.ph && A.PhotoRegistry.speciesCandidate(d.ph, d.ph[1], 1, d.phm); if (c) A.PhotoRegistry.register(P.PHOTOS, d.l, c);
      var ph = d.l && P.photoOf({ latin: d.l }), b = document.getElementById("sp-img");
      if (ph && b) { var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; P.bindPhoto(im, ph); im.src = ph.src; b.innerHTML = ""; b.appendChild(im); }
      if (ph && d.pl) {   /* a larger copy (400 px) exists: a wide photo above the title instead of the small square (#421) */
        var big = document.createElement("img"), art = PV.querySelector("article"); big.className = "jphoto"; big.alt = ""; big.referrerPolicy = "no-referrer";
        big.onload = function () { art.classList.add("bigphoto"); }; big.onerror = function () { big.remove(); }; big.src = ph.src.replace("/species/", "/species-lg/");
        art.insertBefore(big, art.querySelector(".jhero"));
      }
      P.fillPhotos("spcredit", ph && b.querySelector("img") ? [P.creditHTML(ph), "Species photos: Wikipedia"] : []);
      if (!d.l) return;
      M.spN = d.n || d.l; M.spL = d.l;
      [["ea", "What it eats"], ["eb", "What eats it"], ["rl", "Related species"]].forEach(function (x) {   /* from the food webs of the atlas (#447): the links found in the most places; related species of the same family (#448) */
        if (!d[x[0]]) return;
        var w = document.createElement("div"); w.innerHTML = "<h3>" + x[1] + "</h3>"; w.appendChild(strip(d[x[0]]));
        PV.querySelector("article").insertBefore(w, PV.querySelector(".srcd"));
      });
      P.sppPlaces(d.l).then(function (ids) {   /* where it lives: the first ten places in page order as rows, the rest on the map */
        ids = ids.filter(function (i) { return P.ECO_BY[i]; });
        if (M.sid !== sid || !ids.length) return;
        var w = document.createElement("div"), cc = {}, ct = {};   /* where it lives (#445): the countries and continents of all its places, most places first */
        ids.forEach(function (i) { var e = P.ECO_BY[i]; (e.countries || []).forEach(function (c) { cc[c] = (cc[c] || 0) + 1; }); (e.conts || []).forEach(function (c) { ct[c] = (ct[c] || 0) + 1; }); });
        function top(o, n) { var k = Object.keys(o).sort(function (a, b) { return o[b] - o[a] || (a < b ? -1 : 1); }); return k.slice(0, n).map(P.nm).join(", ") + (k.length > n ? " and " + (k.length - n) + " more" : ""); }
        w.innerHTML = "<h3>Found in " + ids.length + " place" + (ids.length > 1 ? "s" : "") + '</h3><p class="fine where">' + (Object.keys(cc).length ? "Countries: " + escH(top(cc, 5)) + " \u00b7 " : "") + "Continents: " + escH(top(ct, 7)) + '</p><div class="prow">' + ids.slice(0, 10).map(function (i) {
          var e = P.ECO_BY[i];
          return '<button type="button" class="pmc ppc" data-spp="' + i + '"><span class="pbox"><span class="pph" data-pid="e-' + i + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (P.ICONS[e.icon] || "") + "</svg></span></span><b>" + escH(e.short) + "</b><small>" + escH(e.place || "") + "</small></button>";
        }).join("") + "</div>" + (ids.length > 10 ? '<p class="fine">Showing 10 of ' + ids.length + ".</p>" : "") + '<p class="fine"><a href="#" data-spmap="1">Show ' + (ids.length > 1 ? "them" : "it") + " on the map</a></p>";
        PV.querySelector("article").insertBefore(w, PV.querySelector(".srcd"));
        ids.slice(0, 10).forEach(function (i) { var o = P.ECO_BY[i]; if (o.imgwiki) { if (!o.li) P.makeCard(o); P.pWant({ isPage: true, eco: sid, id: "e-" + i, wiki: o.imgwiki }); } });
      });
    });
  }
  PV.addEventListener("click", function (ev) {
    var r = M.sid && ev.target.closest("[data-latin]"); if (r) { A.go(r.getAttribute("data-latin"), M.spN); return; }   /* a species in "What it eats" opens its page; Back says this species' name */
    var t = M.sid && ev.target.closest("[data-pback],[data-spp],[data-spmap],[data-sg]"); if (!t) return;
    ev.preventDefault();
    if (t.hasAttribute("data-sg")) { M.sid = null; PV.hidden = true; P.showMap(); P.setTab("species"); openGroup(t.getAttribute("data-sg")); }   /* the group's list in the Species tab */
    else if (t.hasAttribute("data-pback")) P.closeSpecies();
    else if (t.hasAttribute("data-spp")) { M.pushNext = true; P.showPlace(t.getAttribute("data-spp")); }   /* a place opened from the page is a step Back undoes */
    else P.speciesMap(M.spN, M.spL);
  });
  return {
    mapHead: function (hd, r) {   /* map mode: the title is a back link to the search or the species page the map came from (#503); ✕ closes the map mode and goes home; the region trail sits under the title (owner, 9 Nov) */
      hd.innerHTML = '<a href="#" data-hx="1">\u2039 <b>' + P.escH(r.name) + '</b></a> \u00b7 in <span id="qhn"></span> \u00b7 <a href="#" data-hsp="' + A.esc(r.latin) + '">Species page \u203a</a><button type="button" class="qx" data-hclose="1" aria-label="Close and go to the start">\u2715</button>';
      mmStyle(); var tr = document.getElementById("qtrail"); if (!tr) { tr = document.createElement("div"); tr.id = "qtrail"; tr.className = "qtrail"; hd.parentNode.insertBefore(tr, document.getElementById("regions")); }
      M.mapT = function () {   /* the trail is the one the sheet title keeps (World › North America › US); in map mode it is drawn here, not at the top */
        var sr = document.getElementById("srow"), l = sr && sr.querySelector(".strl"), c = sr && sr.querySelector(".stt");
        tr.innerHTML = l && c ? l.innerHTML + '<span class="cur" aria-current="page">' + P.escH(c.textContent) + "</span>" : ""; tr.hidden = !tr.innerHTML;
      };
      if (!hd._c) { hd._c = 1; hd.addEventListener("click", function (ev) {
        if (!ev.target.closest("[data-hclose]")) return; ev.preventDefault(); ev.stopPropagation();
        document.getElementById("qclr").click(); P.setTab("places"); if (M.go) M.go("world", "");   /* no search, no species filter, the Places tab, the whole world */
      }, true); }
      if (!M.mapTO) { M.mapTO = new MutationObserver(function () { if (M.mapT) M.mapT(); }); M.mapTO.observe(document.getElementById("srow"), { childList: true }); }
      M.mapN = function () { var n = M.nPlaces == null || P.FL.busy ? r.n : M.nPlaces, e = document.getElementById("qhn"); if (e) e.textContent = n + (n === 1 ? " place" : " places"); }; M.mapN(); M.mapT(); if (M.setSheet && M.sheetState === "min") M.setSheet("half");
    },
    mapBack: function () {
      var f = M.mFrom, q = document.getElementById("q");
      if (f && f[0]) { q.value = f[0]; q.dispatchEvent(new Event("input", { bubbles: true })); } else if (f) A.go(f[1], "Search"); else document.getElementById("qclr").click();
    },
    show: show,
    open: function () {
      if (started) { shown = null; find(); return; } started = true;
      Promise.all([A.Data.speciesTab("top.json"), A.Data.speciesTab("groups.json")]).then(function (r) { top = r[0]; groups = r[1]; home(); shown = ""; find(); if (want) { openGroup(want); want = null; } })
        .catch(function () { started = false; box.innerHTML = '<p class="fine">The species could not be loaded. Check your connection and try again.</p>'; });
    }
  };
};
