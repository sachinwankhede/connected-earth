  /* ---------- Graph scaffolding ---------- */
  var defs, guideG, guide, root, edgeG, nodeG, edge = null, node = null;

  var drag;

  function build() {
    edgeG.selectAll("*").remove();
    nodeG.selectAll("*").remove();
    defs.selectAll("clipPath").remove();
    NODES.forEach(function (n) { defs.append("clipPath").attr("id", "clip-" + n.id).append("circle").attr("r", n.r - 1.8); });

    edge = edgeG.selectAll("path").data(EDGES).join("path")
      .attr("class", function (e) { return "edge" + (e.kind === "eats" ? "" : " " + e.kind); })
      .attr("marker-end", "url(#arr)");

    node = nodeG.selectAll("g").data(NODES, function (d) { return d.id; }).join("g")
      .attr("class", "node").attr("tabindex", 0).attr("role", "button")
      .attr("aria-label", function (d) { return d.name + ", " + kindText(d).replace("TL " + d.tl + " · ", ""); })
      .call(drag)
      .on("click", function (ev, d) { ev.stopPropagation(); select(d.id); })
      .on("keydown", function (ev, d) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(d.id); } })
      .on("pointerenter", function (ev, d) { if (ev.pointerType === "mouse" && !state.sel) { state.hov = d.id; apply(); } })
      .on("pointerleave", function () { if (state.hov) { state.hov = null; apply(); } });
    node.append("circle").attr("class", "hit").attr("r", function (d) { return d.r + 8; });
    var body = node.append("g").attr("class", "body");
    body.filter(function (d) { return d.cat !== "abiotic"; }).append("circle").attr("class", "core").attr("r", function (d) { return d.r; }).style("fill", colorVar);
    body.filter(function (d) { return d.cat === "abiotic"; }).append("rect").attr("class", "core").attr("rx", 999)
      .attr("x", function (d) { return -d.r; }).attr("y", function (d) { return -d.r; })
      .attr("width", function (d) { return 2 * d.r; }).attr("height", function (d) { return 2 * d.r; }).style("fill", colorVar);
    body.append("g").attr("class", "glyph")
      .attr("transform", function (d) { var s = d.r * 1.4; return "translate(" + (-s / 2) + "," + (-s / 2) + ") scale(" + (s / 24) + ")"; })
      .html(function (d) { return ICONS[d.ic] || ""; });
    body.filter(function (d) { return d.badge; }).append("circle").attr("class", "ring").attr("r", function (d) { return d.r + 5; });
    node.append("text").attr("class", "label").attr("y", function (d) { return d.r + 13; }).attr("text-anchor", "middle").each(function (d) { d3.select(this).selectAll("tspan").data(labLines(d.name)).enter().append("tspan").attr("x", 0).attr("dy", function (l, i) { return i ? "1.08em" : 0; }).text(function (l) { return l; }); });
    node.filter(function (d) { return d.xl || d.fl; }).append("g").attr("class", "xlb").html('<circle r="8"/><text text-anchor="middle" y="3.5">\u2194</text>');
    var delta = node.append("g").attr("class", "delta").style("display", "none");
    delta.append("rect").attr("height", 16).attr("rx", 3);
    delta.append("text").attr("x", 5).attr("y", 11.5);
  }

  function edgePath(e) {
    var s = e.source, t = e.target;
    var dx = t.x - s.x, dy = t.y - s.y, len = Math.hypot(dx, dy) || 1;
    var bend = Math.min(0.14 * len, 50);
    var mx = (s.x + t.x) / 2 - dy / len * bend, my = (s.y + t.y) / 2 + dx / len * bend;
    var ux = mx - s.x, uy = my - s.y, ul = Math.hypot(ux, uy) || 1;
    var vx = t.x - mx, vy = t.y - my, vl = Math.hypot(vx, vy) || 1;
    var sx = s.x + ux / ul * (vrad(s) + 2), sy = s.y + uy / ul * (vrad(s) + 2);
    var tx = t.x - vx / vl * (vrad(t) + 4), ty = t.y - vy / vl * (vrad(t) + 4);
    return "M" + sx + "," + sy + "Q" + mx + "," + my + " " + tx + "," + ty;
  }
  function ticked() {
    if (!node) return;
    edge.attr("d", function (e) { return typeof e.source === "object" && typeof e.target === "object" ? edgePath(e) : null; });
    node.attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
  }

  /* ---------- Forces ---------- */
  var sim = { stop: function () {}, alpha: function () { return { restart: function () {} }; } };   /* stands in until the library has arrived */
  var LAYOUT_CACHE = Object.create(null), LAYOUT_CACHE_ORDER = [], activeLayoutKey = null, cacheAfterResize = false;
  /* the diagram library is not in the page: it arrives as d3-__D3VER__.js (about 280 KB) when a food web or journey map is first opened, or in the quiet time after the map */
  var D3Q = [], D3S = 0;
  function loadD3() {
    if (window.d3 || D3S) return;
    D3S = 1;
    var early = document.querySelector("script[data-d3]");
    if (early) {   /* already asked for in the page head */
      early.addEventListener("load", function () { D3S = 2; var q = D3Q; D3Q = []; q.forEach(function (f) { f(); }); });
      early.addEventListener("error", function () { D3S = 0; var q = D3Q; D3Q = []; q.forEach(function (f) { f(false); }); });
      return;
    }
    var b = location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "");
    var sc = document.createElement("script"); sc.async = true; sc.src = b + "d3-__D3VER__.js";
    sc.onload = function () { D3S = 2; var q = D3Q; D3Q = []; q.forEach(function (f) { f(); }); };
    sc.onerror = function () { D3S = 0; var q = D3Q; D3Q = []; q.forEach(function (f) { f(false); }); };
    document.head.appendChild(sc);
  }
  var WEBINIT = false;
  function withD3(cb) {
    if (window.d3) { if (!WEBINIT) { WEBINIT = true; initWeb(); } cb(true); return; }
    D3Q.push(function (ok) { if (ok === false) { cb(false); return; } withD3(cb); });
    loadD3();
  }
  function initWeb() {
    svg = d3.select("#svg"); cur = d3.zoomIdentity;
  defs = svg.append("defs");
  ["arr", "arr-on"].forEach(function (id) {
    defs.append("marker").attr("id", id).attr("viewBox", "0 0 8 8").attr("refX", 7).attr("refY", 4)
      .attr("markerWidth", 7).attr("markerHeight", 7).attr("markerUnits", "userSpaceOnUse").attr("orient", "auto")
      .append("path").attr("d", "M0,0.5 L7.5,4 L0,7.5 z").attr("class", "arrowhead" + (id === "arr-on" ? " on" : ""));
  });
  guideG = svg.append("g").attr("class", "guides");
  guide = guideG.selectAll("g").data([4, 3, 2, 1, 0]).join("g");
  guide.append("line");
  guide.append("text").text(function (d) { return ({ 4: "Top predators", 3: "Hunters & scavengers", 2: "Plant-eaters", 1: "Plants", 0: "Environment" })[d]; });
  root = svg.append("g").attr("class", "root");
  edgeG = root.append("g");
  nodeG = root.append("g");
  drag = d3.drag()
    .on("start", function (ev, d) { if (!ev.active) sim.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", function (ev, d) { d.fx = ev.x; d.fy = ev.y; })
    .on("end", function (ev, d) { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; });
  sim = d3.forceSimulation()
    .force("link", d3.forceLink().id(function (d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("collide", d3.forceCollide())
    .force("x", d3.forceX())
    .force("y", d3.forceY())
    .alphaDecay(0.04)
    .on("tick", ticked)
    .on("end", function () {
      if (pendingFit) {
        pendingFit = false;
        stretchWeb();
        fit(true);
        if (activeLayoutKey) rememberLayout(activeLayoutKey);
      }
      if (cacheAfterResize) {
        cacheAfterResize = false;
        if (activeLayoutKey) rememberLayout(activeLayoutKey);
      }
    });
  sim.stop();
  zoom = d3.zoom().scaleExtent([0.3, 3]).on("zoom", function (ev) {
    cur = ev.transform;
    root.attr("transform", cur);
    if (ev.sourceEvent) { userMoved = true; document.getElementById("webctl").classList.add("moved"); }
    drawGuides();
  });
  svg.call(zoom).on("dblclick.zoom", null);
  svg.on("click", function () { clearSel(); });
  }
  function layoutKey(id) {
    return JSON.stringify([
      id, PH, state.mode, state.env, W, H, stage.clientWidth, stage.clientHeight,
      NODES.map(function (n) { return [n.id, n.cat || "", n.tl, n.xh, n.r, n.lw]; }),
      EDGES.map(function (e) { return [e.s, e.t, e.kind]; })
    ]);
  }
  function rememberLayout(key) {
    LAYOUT_CACHE[key] = NODES.map(function (n) { return [n.x, n.y]; });
    LAYOUT_CACHE_ORDER = LAYOUT_CACHE_ORDER.filter(function (k) { return k !== key; });
    LAYOUT_CACHE_ORDER.push(key);
    if (LAYOUT_CACHE_ORDER.length > 12) delete LAYOUT_CACHE[LAYOUT_CACHE_ORDER.shift()];
  }

  function stretchWeb() {
    if (!(PH && state.mode === "web")) return;
    var vs = NODES.filter(isVis), cw0 = stage.clientWidth || 390, ch0 = Math.max(240, (stage.clientHeight || 700) - 64);
    var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    vs.forEach(function (d) { x0 = Math.min(x0, d.x); x1 = Math.max(x1, d.x); y0 = Math.min(y0, d.y); y1 = Math.max(y1, d.y); });
    var bw = (x1 - x0) + 90, bh = (y1 - y0) + 90, want = (ch0 / cw0) * bw, sy = Math.max(1, Math.min(2.4, want / bh)), cy0 = (y0 + y1) / 2;
    if (sy > 1.05) { vs.forEach(function (d) { d.y = cy0 + (d.y - cy0) * sy; }); ticked(); }
  }
  function settleNow() {
    sim.stop(); sim.alpha(0.9);
    for (var i = 0; i < 170; i++) sim.tick();
    stretchWeb(); ticked(); pendingFit = false; fit(false); drawGuides();
  }
  function configure() {
    var L = state.mode === "layers";
    sim.force("link").distance(L ? 110 : 95).strength(L ? 0.015 : 0.3);
    sim.force("charge").strength(L ? -60 : -380);
    sim.force("collide").radius(function (d) { return L ? Math.max(d.r + (PH ? 16 : 10), d.lw / 2 + 4) : d.r + 16; }).strength(0.9);
    sim.force("x").x(function (d) { return L ? PAD + d.xh * (W - 2 * PAD) : W / 2; }).strength(L ? 0.25 : (PH ? 0.16 : 0.07));
    sim.force("y").y(function (d) { return L ? rowY(d.tl) : H / 2; }).strength(L ? 0.85 : (PH ? 0.02 : 0.07));
  }

  /* ---------- Zoom and fit ---------- */
  var zoom;

  function drawGuides() {
    var w = stage.clientWidth;
    guide.each(function (d) {
      var y = cur.applyY(rowY(d)), g = d3.select(this);
      g.style("display", d === 0 && !state.env ? "none" : null);
      g.select("line").attr("x1", 0).attr("x2", w).attr("y1", y).attr("y2", y);
      var tp = Infinity; NODES.forEach(function (n) { if (n.tl === d && isVis(n)) tp = Math.min(tp, cur.applyY(n.y) - n.r * cur.k); });
      g.select("text").attr("x", 12).attr("y", isFinite(tp) ? tp - 7 : y - 8 - (PH ? 44 : 22) * Math.min(1, cur.k));
    });
  }
  function fit(animate) {
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    NODES.filter(isVis).forEach(function (d) {
      var hw = Math.max(d.r, d.lw / 2);
      minX = Math.min(minX, d.x - hw); maxX = Math.max(maxX, d.x + hw);
      minY = Math.min(minY, d.y - d.r - (PH ? 54 : 26)); maxY = Math.max(maxY, d.y + d.r + 18);
    });
    if (!isFinite(minX)) return;
    var cw = stage.clientWidth || 900, ch = stage.clientHeight || 560;
    if (cw < 560) ch -= 30;
    var k = Math.min(cw / (maxX - minX + 56), ch / (maxY - minY + 56));
    k = Math.max(0.3, Math.min(1.3, k));
    var t = d3.zoomIdentity.translate(cw / 2 - k * (minX + maxX) / 2, ch / 2 - k * (minY + maxY) / 2).scale(k);
    if (animate && !reduce) svg.transition().duration(500).call(zoom.transform, t);
    else svg.call(zoom.transform, t);
    userMoved = false; document.getElementById("webctl").classList.remove("moved");
  }

  /* ---------- Focus: hover previews direct links, selection pins them, trace follows energy upward ---------- */
  function flows(e) { return visE(e) && e.kind !== "det" && BY[e.s].cat !== "decomp"; }
  function ancestors(id) {
    var seen = new Set(), q = [id];
    while (q.length) {
      var c = q.pop();
      adj.ins[c].forEach(function (e) { if (flows(e) && !seen.has(e.s)) { seen.add(e.s); q.push(e.s); } });
    }
    seen.delete(id);
    return seen;
  }
  function focusInfo(id, trace) {
    var nset = new Set([id]), eset = new Set();
    if (trace) {
      ancestors(id).forEach(function (a) { nset.add(a); });
      EDGES.forEach(function (e) { if (flows(e) && nset.has(e.t) && nset.has(e.s)) eset.add(e); });
    } else {
      INS(id).forEach(function (e) { eset.add(e); nset.add(e.s); });
    }
    OUTS(id).forEach(function (e) { eset.add(e); nset.add(e.t); });
    return { nset: nset, eset: eset };
  }
  function apply() {
    if (!node) return;
    var id = state.sel || state.hov;
    if (!id) {
      node.classed("dim", false).classed("sel", false);
      edge.classed("dim", false).classed("on", false).classed("rip", function (e) { return hasEdits() && rippleEdge(e); }).attr("marker-end", "url(#arr)");
      return;
    }
    var f = focusInfo(id, !!state.sel && state.trace);
    var ripple = hasEdits();
    node.classed("dim", function (d) { return ripple ? false : !f.nset.has(d.id); }).classed("sel", function (d) { return d.id === state.sel; });
    edge.classed("dim", function (e) { return ripple ? false : !f.eset.has(e); }).classed("rip", function (e) { return ripple && rippleEdge(e) && !f.eset.has(e); }).classed("on", function (e) { return f.eset.has(e); })
      .attr("marker-end", function (e) { return f.eset.has(e) ? "url(#arr-on)" : "url(#arr)"; });
  }
  function eff() {
    var m = {}, xs = XL[state.eco] || {};
    Object.keys(xs).forEach(function (nid) {
      var s = xs[nid]; if (!s.other || s.dir === "out") return;
      var ov = (EDITS[s.other.eco] || {})[s.other.node];
      if (ov) m[nid] = Math.round(ov * COUPLE);
    });
    Object.keys(state.edits).forEach(function (k) { m[k] = state.edits[k]; });
    return m;
  }
  function hasEdits() { var pe = eff(); return Object.keys(pe).some(function (k) { return BY[k] && isVis(BY[k]); }); }
  function rippleEdge(e) { var x = state.fx; return x && (Math.abs(x[e.s] || 0) >= 1 && Math.abs(x[e.t] || 0) >= 1); }
  var focusMoved = false;
  function focusSel(id) {
    var d = BY[id]; if (!d || !isFinite(d.x)) return;
    var ch = stage.clientHeight || 700, cw = stage.clientWidth || 390, visH = ch - Math.round(window.innerHeight * 0.46) - 8;
    var y = cur.applyY(d.y), x = cur.applyX(d.x);
    if (y > visH - 44 || y < 60 || x < 36 || x > cw - 36) focusMoved = true, svg.transition().duration(380).call(zoom.translateTo, d.x, d.y, [cw / 2, Math.max(70, visH * 0.5)]);
  }
  function select(id) { var nn = BY[id]; if (nn && nn.cat && !state.env) setEnv(true);   /* an environment item can only be seen with the environment shown */
    state.sel = id; state.hov = null; renderPanel(); apply(); panel.scrollTop = 0; if (PH) focusSel(id); }
  function clearSel() { if (!state.sel && !state.hov) return; state.sel = null; state.hov = null; renderPanel(); apply(); if (PH && focusMoved) { focusMoved = false; fit(true); } }

