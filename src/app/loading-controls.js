  /* ---------- Loading an ecosystem ---------- */
  function applyEnv() {
    sim.nodes(NODES.filter(isVis));
    sim.force("link").links(EDGES.filter(visE));
    node.style("display", function (d) { return isVis(d) ? null : "none"; });
    edge.style("display", function (e) { return visE(e) ? null : "none"; });
    updateStats();
  }
  function nodeName(ecoId, nodeId) { var e = ECO_BY[ecoId], n = e.nodes && e.nodes.filter(function (q) { return q.id === nodeId; })[0]; return n ? n.name : (e.idx.cx[nodeId] || nodeId); }
  /* a place's full web (species, links, evidence) is fetched the first time it is opened */
  /* opening a place also waits for the species index, so "Shares species with" and "Also found in" are complete the first time they show */
  function fetchWeb(id) {
    return fetchWebData(id).then(function (ok) {
      var e = ECO_BY[id];
      if (ok && !Places.done && e.rel && e.rel.some(function (x) { return !ECO_BY[x[0]]; })) return Places.loadLocals().then(function () { return true; });   /* a related place that is local must be there to be drawn */
      return ok;
    });
  }
  function fetchWebData(id) {
    var e = ECO_BY[id];
    if (e.nodes) return Promise.resolve(true);
    if (!e._wp) e._wp = Data.place(id).then(function (w) { e.nodes = w.nodes; e.raw = w.raw; e.ev = w.ev; e.sources = w.sources; e.notes = w.notes; e.tip = w.tip; e.rel = PILOT && w.relp ? w.relp : (w.rel || []); e.story = w.story; e.matters = w.matters; e.summary = w.summary;
      if (w.ph) { e.phLocal = true; Object.keys(w.ph).forEach(function (t) { var c = PhotoRegistry.speciesCandidate(w.ph[t], w.ph[t] && w.ph[t][1], 1, (w.phm || {})[t]); if (c) PhotoRegistry.register(PHOTOS, t, c); }); }   /* this place's own species pictures: no list of every species is needed to show them */
      return true; }).catch(function () { e._wp = null; return false; });
    return e._wp;
  }
  function loadEco(id) {
    sim.stop();
    cacheAfterResize = false;
    ECO = ECO_BY[id];
    state.eco = id; state.sel = null; state.hov = null; state.edits = EDITS[id] = EDITS[id] || {}; state.fx = {};
    NODES = ECO.nodes; BY = {}; adj = { ins: {}, outs: {} };
    NODES.forEach(function (n) {
      BY[n.id] = n; adj.ins[n.id] = []; adj.outs[n.id] = [];
      var xs = XL[id] && XL[id][n.id]; n.xl = xs && xs.other ? xs : null; n.fl = xs && !xs.other ? xs.link : null;
      n.k = 1; n.photoShown = false; n.fx = null; n.fy = null; n.vx = 0; n.vy = 0;
    });
    EDGES = ECO.raw.map(function (r) { return { source: r[0], target: r[1], s: r[0], t: r[1], kind: KIND[r[2]] || "eats" }; });
    EDGES.forEach(function (e) { adj.outs[e.s].push(e); adj.ins[e.t].push(e); });
    NODES.forEach(function (n) {
      var deg = adj.ins[n.id].length + adj.outs[n.id].length;
      n.r = PH ? Math.min(32, 21 + 2.2 * Math.sqrt(deg)) : Math.min(26, 12 + 2.2 * Math.sqrt(deg));
      n.r0 = n.r;
      n.lw = Math.max.apply(null, labLines(n.name).map(function (l) { return l.length; })) * 6.1;
    });
    build();
    applyEnv();
    renderPanel();
    dims();
    var key = layoutKey(id), cached = LAYOUT_CACHE[key], cacheHit = !!cached && cached.length === NODES.length;
    activeLayoutKey = key;
    M.layoutInfo = { cacheHit: cacheHit, ticks: cacheHit ? 0 : 120 };
    if (cacheHit) NODES.forEach(function (d, i) { d.x = cached[i][0]; d.y = cached[i][1]; });
    else NODES.forEach(function (d, i) {
      d.x = PAD + d.xh * (W - 2 * PAD) + Math.sin(i * 7.1) * 6;
      d.y = rowY(d.tl) + Math.cos(i * 3.7) * 6;
    });
    configure();
    if (!cacheHit) {
      for (var i = 0; i < 120; i++) sim.tick();
      rememberLayout(key);
    } else {
      LAYOUT_CACHE_ORDER = LAYOUT_CACHE_ORDER.filter(function (k) { return k !== key; });
      LAYOUT_CACHE_ORDER.push(key);
    }
    ticked();
    cur = d3.zoomIdentity;
    fit(false);
    drawGuides();
    paint();
    apply();
    el.h1.textContent = ECO.name;
    loadPhotos();
    
  }

  /* ---------- Controls ---------- */
  function gMode(m) {
    if (m === state.mode) return;
    state.mode = m;
    var wc0 = document.getElementById("webctl"); wc0.setAttribute("data-mode", m); document.getElementById("vt").setAttribute("aria-label", m === "layers" ? "Show web view" : "Show layers view"); document.getElementById("vt").setAttribute("title", m === "layers" ? "Show web view" : "Show layers view"); var vtt = document.getElementById("vtoast"); vtt.textContent = m === "layers" ? "Layers: who eats whom, by level" : "Web: everything connected"; vtt.classList.add("on"); clearTimeout(vtt._t); vtt._t = setTimeout(function () { vtt.classList.remove("on"); }, 1500);
    document.getElementById("m-layers").setAttribute("aria-pressed", String(m === "layers"));
    document.getElementById("m-web").setAttribute("aria-pressed", String(m === "web"));
    dims(); configure();
    guideG.classed("off", m !== "layers");
    drawGuides();
    settleNow();
  }
  function setEnv(on) {
    if (on === state.env) return;
    state.env = on;
    document.getElementById("env").setAttribute("aria-pressed", String(on));
    if (state.sel && BY[state.sel] && !isVis(BY[state.sel])) state.sel = null;
    state.hov = null;
    applyEnv();
    dims(); configure(); drawGuides(); paint(); renderPanel(); apply();
    settleNow();
  }
  document.getElementById("m-layers").addEventListener("click", function () { gMode("layers"); });
  document.getElementById("m-web").addEventListener("click", function () { gMode("web"); });
  document.getElementById("fit").addEventListener("click", function () { fit(true); });
  document.getElementById("env").addEventListener("click", function () { setEnv(!state.env); });
  document.getElementById("env").setAttribute("aria-pressed", String(state.env));
  document.getElementById("env").setAttribute("aria-label", "Show environment");
  el.reset.addEventListener("click", clearEdits);
  [["env", "Show environment: sun, rain, soil"], ["share", "Copy link to this ecosystem"], ["fit", "Fit everything on screen"], ["moreb", "More"], ["vt", "Show web view"]].forEach(function (a) { var b = document.getElementById(a[0]); if (b) { b.setAttribute("aria-label", a[1]); b.setAttribute("title", a[1]); } });
  stage.appendChild(document.getElementById("webctl")); stage.appendChild(document.getElementById("vtoast")); stage.appendChild(document.getElementById("pbk")); (function () { var g = document.createElement("span"); g.className = "gsh"; g.innerHTML = shareBtn(); stage.appendChild(g); })(); stage.appendChild(document.getElementById("gcap"));
  (function () { var wc = document.getElementById("webctl"), mb = document.getElementById("moreb"); wc.setAttribute("data-mode", state.mode); document.getElementById("vt").addEventListener("click", function () { gMode(state.mode === "layers" ? "web" : "layers"); }); mb.addEventListener("click", function () { var o = wc.classList.toggle("mopen"); mb.setAttribute("aria-expanded", String(o)); }); ["share", "fit"].forEach(function (i) { document.getElementById(i).addEventListener("click", function () { wc.classList.remove("mopen"); mb.setAttribute("aria-expanded", "false"); }); }); })();

  var rt;
  if (window.ResizeObserver) {
    new ResizeObserver(function () {
      clearTimeout(rt);
      rt = setTimeout(function () {
        if (!ECO || !stage.clientWidth) return;
        var ow = W, oh = H;
        dims();
        if (ow === W && oh === H) {
          if (!userMoved) fit(false);
          drawGuides();
          if (!cacheAfterResize) {
            activeLayoutKey = layoutKey(state.eco);
            rememberLayout(activeLayoutKey);
          }
          return;
        }
        configure(); drawGuides();
        pendingFit = !userMoved;
        activeLayoutKey = layoutKey(state.eco);
        cacheAfterResize = true;
        sim.alpha(0.5).restart();
      }, 120);
    }).observe(stage);
  }

