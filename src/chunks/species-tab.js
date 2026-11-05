/* The Species tab (#422). This code is not in the page: the page loads this file the first time the tab opens (withSpeciesTab in src/app/cards.js) and gives it what it
   needs in A (Data, the photo registry, escaping, the row icons, and go(latin) which opens a species page). It reads api/species-tab/ only through A.Data.
   First screen: the species found in the most places, then the groups; a group opens its own list, 250 rows at a time. */
window.__chunk = window.__chunk || {};
window.__chunk["species-tab"] = function (A) {
  var box = document.getElementById("sptab"), started = false, top = [], groups = [];
  function el(html, cls) { var d = document.createElement("div"); d.className = cls; d.innerHTML = html; return d; }
  function row(r) {   /* [Latin name, usual name, places, picture file or 0] */
    var c = r[3] && A.PhotoRegistry.speciesCandidate([r[3], r[0]], r[0], 1, null);
    var d = el('<span class="sgi">' + (c ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + A.esc(c.assetUrl) + '">' : A.leaf) + '</span><span class="sgt"><b></b><i></i></span>' + A.chev, "sgr");
    d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-latin", r[0]);
    d.querySelector("b").textContent = r[1]; d.querySelector("i").textContent = "Species · in " + r[2] + (r[2] === 1 ? " place" : " places");
    var im = d.querySelector("img"); if (im) im.onerror = function () { d.querySelector(".sgi").innerHTML = A.leaf; };
    return d;
  }
  function groupRow(g) {   /* [key, label, species, pages] */
    var d = el('<span class="sgi">' + A.leaf + '</span><span class="sgt"><b></b><i></i></span>' + A.chev, "sgr");
    d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-g", g[0]);
    d.querySelector("b").textContent = g[1]; d.querySelector("i").textContent = g[2] + (g[2] === 1 ? " species" : " species");
    return d;
  }
  function list(items, make) { var l = el("", "sgl"); items.forEach(function (x) { l.appendChild(make(x)); }); return l; }
  function home() {
    box.innerHTML = "<h3>Found in the most places</h3>"; box.appendChild(list(top, row));
    box.insertAdjacentHTML("beforeend", "<h3>Browse by group</h3>"); box.appendChild(list(groups, groupRow));
  }
  function group(g) {   /* one group: its first page, and "Show more" for the next */
    var page = 0, shown = 0;
    box.innerHTML = '<button type="button" class="jback" data-up="1">‹ Species</button><h3></h3>';
    box.querySelector("h3").textContent = g[1] + " · " + g[2];
    var l = el("", "sgl"), p = el('<a href="#" data-more="1"></a>', "fine"); box.appendChild(l); box.appendChild(p); p.hidden = true;
    function more() {
      var k = page++;
      A.Data.speciesTab("g-" + g[0] + "-" + k + ".json").then(function (rows) {
        rows.forEach(function (r) { l.appendChild(row(r)); }); shown += rows.length;
        p.hidden = shown >= g[2]; p.firstChild.textContent = "Show " + Math.min(g[2] - shown, 250) + " more ›";
      }).catch(function () { page = k; p.hidden = false; p.firstChild.textContent = "Could not load. Try again"; });
    }
    p.addEventListener("click", function (ev) { ev.preventDefault(); more(); });
    more();
  }
  function act(t) {
    var d = t.closest(".sgr"), g;
    if (d && d.hasAttribute("data-latin")) A.go(d.getAttribute("data-latin"));
    else if (d && (g = groups.filter(function (x) { return x[0] === d.getAttribute("data-g"); })[0])) group(g);
    else if (t.closest("[data-up]")) { home(); box.scrollIntoView && box.scrollIntoView({ block: "start" }); }
  }
  var qIn = document.getElementById("q"), qT, qN = 0, shown = "";
  function find() {   /* the search box on this tab looks for species only (#422 step 4) */
    var q = qIn.value.trim(), n = ++qN; if (box.hidden || !started || q === shown) return; shown = q;
    if (q.length < 2) { home(); return; }
    A.find(q).then(function (rows) {
      if (n !== qN || !rows) return;
      box.innerHTML = "";   /* what was found is said in the note under the tabs, the same on all three (#449) */
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
    function page(d) {
      var latin = d.l || words, name = d.n || latin;
      return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">\u2039 ' + escH(M.spFrom || (P.FL.q ? "Search" : "Places")) + "</button>" + P.shareBtn() + "</div>" +
        '<div class="jhero"><span class="jhimg" id="sp-img">' + (P.ICONS[d.ic] ? '<svg viewBox="0 0 24 24" aria-hidden="true">' + P.ICONS[d.ic] + "</svg>" : A.leaf) + '</span><div><p class="jkind">' + escH(P.PNAMES[d.tl] || "Species") + "</p><h2>" + escH(name) + '</h2><p class="jr"><i>' + escH(latin) + "</i></p></div></div>" +
        (d.t ? '<p class="about">' + P.aboutText({ latin: latin, wiki: d.ph && d.ph[1] }) + "</p>" : "") +
        P.footHTML({ photoId: "spcredit", sources: [{ title: "Wikipedia: " + escH(latin), url: "https://en.wikipedia.org/wiki/" + encodeURIComponent(((d.ph && d.ph[1]) || latin).replace(/ /g, "_")) }] }) + "</article>";
    }
    if (M.sid !== sid) return;
    PV.innerHTML = page({});
    A.Data.species(sid).catch(function () { return null; }).then(function (d) {
      if (M.sid !== sid) return;
      d = d || {}; if (d.t) P.ABOUT[sid] = d.t;
      PV.innerHTML = page(d);
      var c = d.ph && A.PhotoRegistry.speciesCandidate(d.ph, d.ph[1], 1, d.phm); if (c) A.PhotoRegistry.register(P.PHOTOS, d.l, c);
      var ph = d.l && P.photoOf({ latin: d.l }), b = document.getElementById("sp-img");
      if (ph && b) { var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; P.bindPhoto(im, ph); im.src = ph.src; b.innerHTML = ""; b.appendChild(im); }
      P.fillPhotos("spcredit", ph && b.querySelector("img") ? [P.creditHTML(ph), "Species photos: Wikipedia"] : []);
      if (!d.l) return;
      M.spN = d.n || d.l; M.spL = d.l;
      P.sppPlaces(d.l).then(function (ids) {   /* where it lives: the first ten places in page order as rows, the rest on the map */
        ids = ids.filter(function (i) { return P.ECO_BY[i]; });
        if (M.sid !== sid || !ids.length) return;
        var w = document.createElement("div");
        w.innerHTML = "<h3>Found in " + ids.length + " place" + (ids.length > 1 ? "s" : "") + '</h3><div class="pjs">' + ids.slice(0, 10).map(function (i) {
          var e = P.ECO_BY[i];
          return '<a class="pj" href="#pg=' + i + '" data-spp="' + i + '"><span class="pph" data-pid="e-' + i + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (P.ICONS[e.icon] || "") + '</svg></span><span class="pjt"><i>' + escH(e.place || "") + "</i><b>" + escH(e.short) + '</b></span><span class="pjgo" aria-hidden="true">\u203a</span></a>';
        }).join("") + "</div>" + (ids.length > 10 ? '<p class="fine">Showing 10 of ' + ids.length + ".</p>" : "") + '<p class="fine"><a href="#" data-spmap="1">Show ' + (ids.length > 1 ? "them" : "it") + " on the map</a></p>";
        PV.querySelector("article").insertBefore(w, PV.querySelector(".srcd"));
        ids.slice(0, 10).forEach(function (i) { var o = P.ECO_BY[i]; if (o.imgwiki) { if (!o.li) P.makeCard(o); P.pWant({ isPage: true, eco: sid, id: "e-" + i, wiki: o.imgwiki }); } });
      });
    });
  }
  PV.addEventListener("click", function (ev) {
    var t = M.sid && ev.target.closest("[data-pback],[data-spp],[data-spmap]"); if (!t) return;
    ev.preventDefault();
    if (t.hasAttribute("data-pback")) P.closeSpecies();
    else if (t.hasAttribute("data-spp")) { M.pushNext = true; P.showPlace(t.getAttribute("data-spp")); }   /* a place opened from the page is a step Back undoes */
    else P.speciesMap(M.spN, M.spL);
  });
  return {
    show: show,
    open: function () {
      if (started) { shown = null; find(); return; } started = true;
      Promise.all([A.Data.speciesTab("top.json"), A.Data.speciesTab("groups.json")]).then(function (r) { top = r[0]; groups = r[1]; home(); shown = ""; find(); })
        .catch(function () { started = false; box.innerHTML = '<p class="fine">The species could not be loaded. Check your connection and try again.</p>'; });
    }
  };
};
