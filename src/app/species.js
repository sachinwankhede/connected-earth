  // ---- species page (#420): what a species is. Its data is one small file (api/species/<id>.json), read when the page opens; without it the page still shows the name ----
  function showSpecies(sid, from) {
    if (FL.q && !M.pid && !M.jid && !M.sid && !M.fromHash) M.pushNext = true;
    M.sid = sid; M.pid = null; M.jid = null; M.loading = null; sim.stop();
    el.mapview.hidden = true; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true; JV.hidden = true;
    var words = sid.replace(/-/g, " ").replace(/^./, function (c) { return c.toUpperCase(); });
    function page(d) {
      var latin = d.l || words, name = d.n || latin;
      return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">‹ ' + (FL.q ? "Search" : "Places") + "</button>" + shareBtn() + "</div>" +
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
    });
  }
  function closeSpecies() {
    if (history.state && history.state.sp && M.sid) { history.back(); return; }   /* a page opened from a search is its own history entry (#412) */
    M.sid = null; PV.hidden = true; showMap();
  }
  PV.addEventListener("click", function (ev) { if (M.sid && ev.target.closest("[data-pback]")) closeSpecies(); });
