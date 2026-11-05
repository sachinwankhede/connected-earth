  // ---- species page (#420): what a species is. Its data is one small file (api/species/<id>.json), read when the page opens; without it the page still shows the name ----
  function showSpecies(sid, from) {
    if (FL.q && !M.pid && !M.jid && !M.sid && !M.fromHash) M.pushNext = true;
    M.spFrom = from || null; M.sid = sid; M.pid = null; M.jid = null; M.loading = null; sim.stop();
    el.mapview.hidden = true; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true; JV.hidden = true;
    var words = sid.replace(/-/g, " ").replace(/^./, function (c) { return c.toUpperCase(); });
    function page(d) {
      var latin = d.l || words, name = d.n || latin;
      return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">‹ ' + escH(M.spFrom || (FL.q ? "Search" : "Places")) + "</button>" + shareBtn() + "</div>" +
        '<div class="jhero"><span class="jhimg" id="sp-img">' + (ICONS[d.ic] ? '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[d.ic] + "</svg>" : SUG_LEAF) + '</span><div><p class="jkind">' + escH(PNAMES[d.tl] || "Species") + "</p><h2>" + escH(name) + '</h2><p class="jr"><i>' + escH(latin) + "</i></p></div></div>" +
        (d.t ? '<p class="about">' + aboutText({ latin: latin, wiki: d.ph && d.ph[1] }) + "</p>" : "") +
        footHTML({ photoId: "spcredit", sources: [{ title: "Wikipedia: " + escH(latin), url: "https://en.wikipedia.org/wiki/" + encodeURIComponent(((d.ph && d.ph[1]) || latin).replace(/ /g, "_")) }] }) + "</article>";
    }
    PV.hidden = false; PV.innerHTML = page({}); PV.scrollTop = 0; window.scrollTo(0, 0); syncHash();
    Data.species(sid).catch(function () { return null; }).then(function (d) {
      if (M.sid !== sid) return;
      d = d || {}; if (d.t) ABOUT[sid] = d.t;
      PV.innerHTML = page(d);
      var c = d.ph && PhotoRegistry.speciesCandidate(d.ph, d.ph[1], 1, d.phm); if (c) PhotoRegistry.register(PHOTOS, d.l, c);
      var ph = d.l && photoOf({ latin: d.l }), b = document.getElementById("sp-img");
      if (ph && b) { var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; bindPhoto(im, ph); im.src = ph.src; b.innerHTML = ""; b.appendChild(im); }
      fillPhotos("spcredit", ph && b.querySelector("img") ? [creditHTML(ph), "Species photos: Wikipedia"] : []);
      if (!d.l) return;
      M.spN = d.n || d.l; M.spL = d.l;
      sppPlaces(d.l).then(function (ids) {   /* where it lives: the first ten places in page order as rows, the rest on the map */
        ids = ids.filter(function (i) { return ECO_BY[i]; });
        if (M.sid !== sid || !ids.length) return;
        var w = document.createElement("div");
        w.innerHTML = "<h3>Found in " + ids.length + " place" + (ids.length > 1 ? "s" : "") + '</h3><div class="pjs">' + ids.slice(0, 10).map(function (i) {
          var e = ECO_BY[i];
          return '<a class="pj" href="#pg=' + i + '" data-spp="' + i + '"><span class="pph" data-pid="e-' + i + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[e.icon] || "") + '</svg></span><span class="pjt"><i>' + escH(e.place || "") + "</i><b>" + escH(e.short) + '</b></span><span class="pjgo" aria-hidden="true">\u203a</span></a>';
        }).join("") + "</div>" + (ids.length > 10 ? '<p class="fine">Showing 10 of ' + ids.length + ".</p>" : "") + '<p class="fine"><a href="#" data-spmap="1">Show ' + (ids.length > 1 ? "them" : "it") + " on the map</a></p>";
        PV.querySelector("article").insertBefore(w, PV.querySelector(".srcd"));
        ids.slice(0, 10).forEach(function (i) { var o = ECO_BY[i]; if (o.imgwiki) { if (!o.li) makeCard(o); pWant({ isPage: true, eco: sid, id: "e-" + i, wiki: o.imgwiki }); } });
      });
    });
  }
  function closeSpecies() {
    if (history.state && history.state.sp && M.sid) { history.back(); return; }   /* a page opened from a search is its own history entry (#412) */
    M.sid = null; PV.hidden = true; showMap();
  }
  PV.addEventListener("click", function (ev) {
    var t = M.sid && ev.target.closest("[data-pback],[data-spp],[data-spmap]"); if (!t) return;
    ev.preventDefault();
    if (t.hasAttribute("data-pback")) closeSpecies();
    else if (t.hasAttribute("data-spp")) { M.pushNext = true; showPlace(t.getAttribute("data-spp")); }   /* a place opened from the page is a step Back undoes */
    else speciesMap(M.spN, M.spL);
  });
