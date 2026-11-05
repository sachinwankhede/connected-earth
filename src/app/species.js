  // ---- species page (#420): what a species is. The first view keeps only the part that must happen at once (the address, hiding the other views); the page itself is built by
  // the lazy chunk (src/chunks/species-tab.js, show()), so the page can grow without taking the first view's size budget (#445) ----
  function showSpecies(sid, from) {
    if (FL.q && !M.pid && !M.jid && !M.sid && !M.fromHash) M.pushNext = true;
    M.spFrom = from || null; M.sid = sid; M.pid = null; M.jid = null; M.loading = null; sim.stop();
    el.mapview.hidden = true; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true; JV.hidden = true;
    PV.hidden = false; PV.innerHTML = ""; PV.scrollTop = 0; window.scrollTo(0, 0); syncHash();
    withSpeciesTab(function (c) { c.show(sid); });
  }
  function closeSpecies() {
    if (history.state && history.state.sp && M.sid) { history.back(); return; }   /* a page opened from a search is its own history entry (#412) */
    M.sid = null; PV.hidden = true; showMap();
  }
