  /* the journey page: opens from a journey card, a route on the map, or a linked food web */
  var JV = document.getElementById("jview");
  function jbyId(id) { return CROSS.filter(function (c) { return c.id === id; })[0]; }
  function jEnds(c) { return ecoEnds(c).map(function (x, i) { return { eco: x.eco, node: x.node, e: ECO_BY[x.eco], flowLabel: c.type === "flow" ? (i === 0 ? "Carried from" : "Carried to") : "" }; }); }
  function jRelated(c) {
    var mine = jEnds(c).map(function (x) { return x.eco; });
    return CROSS.filter(function (o) { return o !== c; }).map(function (o) {
      var sh = jEnds(o).filter(function (x) { return mine.indexOf(x.eco) >= 0; }).length;
      return { o: o, score: sh * 2 + (o.type === c.type ? 1 : 0) };
    }).sort(function (a, b) { return b.score - a.score; }).slice(0, 3).map(function (r) { return r.o; });
  }
  function jRouteSVG(c) {
    var W = Math.max(300, Math.min(720, (JV.clientWidth || 640) - (JV.clientWidth < 740 ? 0 : 0))), H = Math.round(W < 500 ? W * 0.9 : W * 0.5), ab = arcEnds(c), cv = curve(ab[0], ab[1]);
    var mid = (cv[0][0] + cv[cv.length - 1][0]) / 2;
    var lons = cv.map(function (q) { return q[0]; }), lats = cv.map(function (q) { return q[1]; });
    var x0 = Math.min.apply(null, lons), x1 = Math.max.apply(null, lons), y0 = Math.min.apply(null, lats), y1 = Math.max.apply(null, lats);
    var mx = Math.max(9, (x1 - x0) * 0.22), my = Math.max(7, (y1 - y0) * 0.32);
    var corners = [[x0 - mx, Math.max(-84, y0 - my)], [x1 + mx, Math.max(-84, y0 - my)], [x0 - mx, Math.min(84, y1 + my)], [x1 + mx, Math.min(84, y1 + my)]];
    var pr = d3.geoMercator().rotate([-mid, 0]);
    pr.fitExtent([[10, 10], [W - 10, H - 10]], { type: "MultiPoint", coordinates: cv.concat(corners) });
    var gp = d3.geoPath(pr), en = jEnds(c), hot = {};
    en.forEach(function (x) { (x.e.countries || []).forEach(function (n) { hot[n] = 1; }); });
    var land = GJ_C.features.map(function (f) { var d = gp(f); return d ? '<path class="jl' + (hot[f.properties.name] ? " hot" : "") + '" d="' + d + '"/>' : ""; }).join("");
    var coast = gp(GJ_C) || "", grat = gp(d3.geoGraticule10()) || "";
    // satellite tiles sit on top of the plain map; any tile that fails to load leaves the plain map showing through
    var sc = pr.scale(), kx = sc * Math.PI / 180, cx = pr([mid, 0])[0], tz = Math.max(0, Math.min(8, Math.round(Math.log(2 * Math.PI * sc / 256) / Math.LN2))), tn = Math.pow(2, tz), tiles = "";
    function mlat(j) { return 180 / Math.PI * Math.atan(Math.sinh(Math.PI * (1 - 2 * j / tn))); }
    var tlat0 = pr.invert([cx, 0])[1], tlat1 = pr.invert([cx, H])[1];
    function ty(la) { var r = la * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * tn); }
    var j0 = Math.max(0, ty(Math.min(84, tlat0))), j1 = Math.min(tn - 1, ty(Math.max(-84, tlat1))), i0 = Math.floor(((mid + (0 - cx) / kx) + 180) / 360 * tn), i1 = Math.floor(((mid + (W - cx) / kx) + 180) / 360 * tn);
    if ((i1 - i0 + 1) * (j1 - j0 + 1) <= 36) for (var ti = i0; ti <= i1; ti++) for (var tj = j0; tj <= j1; tj++) {
      var tx = cx + ((ti / tn * 360 - 180) - mid) * kx, yA = pr([mid, mlat(tj)])[1], yB = pr([mid, mlat(tj + 1)])[1];
      tiles += '<image class="jt" href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/' + tz + "/" + tj + "/" + (((ti % tn) + tn) % tn) + '" x="' + tx.toFixed(1) + '" y="' + yA.toFixed(1) + '" width="' + (360 / tn * kx + 0.8).toFixed(1) + '" height="' + (yB - yA + 0.8).toFixed(1) + '" preserveAspectRatio="none" opacity="0"/>';
    }
    var pts = cv.map(function (q) { return pr(q); }), d = "M" + pts.map(function (q) { return q[0].toFixed(1) + " " + q[1].toFixed(1); }).join("L");
    function lab(q, name) { var right = q[0] > W * 0.62, below = q[1] < 36; return '<text x="' + (q[0] + (right ? -12 : 12)).toFixed(1) + '" y="' + (q[1] + (below ? 24 : -11)).toFixed(1) + '" text-anchor="' + (right ? "end" : "start") + '">' + escH(name) + "</text>"; }
    var A = pts[0], B = pts[pts.length - 1], flow = c.type === "flow", q = pts[pts.length - 4], ang = Math.atan2(B[1] - q[1], B[0] - q[0]) * 180 / Math.PI;
    var head = flow ? '<path class="jhead" transform="translate(' + B[0].toFixed(1) + " " + B[1].toFixed(1) + ") rotate(" + ang.toFixed(1) + ')" d="M-2 -9 L14 0 L-2 9 Z"/>' : "";
    var dl = Math.min.apply(null, pts.map(function (q) { return Math.hypot(Math.max(0, 10 - q[0], q[0] - 170), Math.max(0, H - 50 - q[1], q[1] - (H - 10))); })), dr = Math.min.apply(null, pts.map(function (q) { return Math.hypot(Math.max(0, W - 170 - q[0], q[0] - (W - 10)), Math.max(0, H - 50 - q[1], q[1] - (H - 10))); }));
    return { pts: pts, right: dr > dl, tiles: tiles, html: '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Route from ' + escH(en[0].e.short) + " to " + escH(en[en.length - 1].e.short) + '"><defs><linearGradient id="jsea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--sea-a)"/><stop offset="1" style="stop-color:var(--sea-b)"/></linearGradient><radialGradient id="jvig" cx=".5" cy=".5" r=".78"><stop offset=".62" stop-color="#0a1e2e" stop-opacity="0"/><stop offset="1" stop-color="#0a1e2e" stop-opacity=".2"/></radialGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#jsea)"/><path class="jgrat" d="' + grat + '"/><path class="jcoast" d="' + coast + '"/>' + land + '<g class="jtiles"></g><rect width="' + W + '" height="' + H + '" fill="url(#jvig)" pointer-events="none"/>' + '<path class="jglow" d="' + d + '"/><path class="jarc" d="' + d + '"/>' + head + '<circle class="jpt' + (flow ? " src" : "") + '" cx="' + A[0].toFixed(1) + '" cy="' + A[1].toFixed(1) + '" r="7"/>' + (flow ? "" : '<circle class="jpt" cx="' + B[0].toFixed(1) + '" cy="' + B[1].toFixed(1) + '" r="7"/>') + lab(A, en[0].e.short) + lab(B, en[en.length - 1].e.short) + '<circle class="jfd" id="jdot" cx="' + A[0].toFixed(1) + '" cy="' + A[1].toFixed(1) + '" r="13"/><text class="jemo" id="jemo" x="' + A[0].toFixed(1) + '" y="' + (A[1] + 1).toFixed(1) + '">' + (c.mark || "") + "</text></svg>" };
  }
  function jPlace(t) { t = String(t).replace(/\s*\([^)]*\)/g, ""); return t.length > 44 ? t.split(",")[0] : t; }
  function jHTML(c, rt) {
    var en = jEnds(c), fi = en[0].e.icon, icon = function (k) { return '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[k] || "") + "</svg>"; };
    var ends = en.map(function (x, i) {
      return '<div class="jend" role="button" tabindex="0" data-jopen="' + x.eco + ":" + x.node + '"><span class="jeimg" id="jp-e' + i + '">' + icon(x.e.icon) + '</span><span class="jet">' + (x.flowLabel ? "<small>" + x.flowLabel + "</small>" : "") + "<b>" + escH(x.e.name) + '</b><span class="jrole" id="jrole' + i + '"></span></span></div>';
    }).join("");
    var src = (c.sources || []).map(function (q) { return '<li><a href="' + esc(q.u) + '" target="_blank" rel="noopener noreferrer">' + escH(q.t) + "</a></li>"; }).join("");
    var more = jRelated(c).map(function (o) { var oe = jEnds(o); return '<button type="button" data-jj="' + o.id + '"><span class="jmimg" id="jm-' + o.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[oe[0].e.icon] || "") + '</svg></span><span class="jmt"><i>' + escH(oe[0].e.short) + " \u2192 " + escH(oe[oe.length - 1].e.short) + "</i><b>" + escH(o.title) + "</b></span></button>"; }).join("");
    return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-jback="1">\u2039 Journeys</button>' + shareBtn() + '</div>' +
      '<div class="jhero"><span class="jhimg" id="jp-main">' + icon(fi) + '</span><div><p class="jkind">' + (c.type === "flow" ? "Nutrients carried" : "Animals that travel") + "</p><h2>" + escH(c.title) + '</h2><p class="jr">' + escH(en[0].e.short) + " <i>\u2192</i> " + escH(en[en.length - 1].e.short) + "</p></div></div>" +
      '<div class="jmap' + (rt.right ? " pr" : "") + '" id="jfly" role="button" tabindex="0" aria-label="' + escH(c.go || "Follow the route") + '">' + rt.html + '<span class="jplay"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 1.5v13l11-6.5z"/></svg>' + escH(c.go || "Follow the route") + '</span><span class="jattr">\u00a9 Esri, Maxar</span></div>' +
      '<p class="fine">Routes are simplified; real journeys vary by season and population.</p>' +
      (c.when ? '<p class="jwhen"><b>When.</b> ' + escH(c.when) + "</p>" : "") +
      "<h3>The story</h3><p>" + escH(c.text) + "</p>" + (c.matters ? '<p class="jwhy"><b>Why it matters.</b> ' + escH(c.matters) + "</p>" : "") +
      '<h3>Places on this route</h3><div class="jends">' + ends + "</div>" +
      (more ? '<h3>More journeys</h3><div class="jmore">' + more + "</div>" : "") +
      footHTML({ sources: c.sources, photoId: "jcredit" }) + "</article>";
  }
  function jRoles(c) {
    var id = c.id;
    jEnds(c).forEach(function (x, i) {
      fetchWeb(x.eco).then(function (ok) {
        var box = document.getElementById("jrole" + i); if (!ok || M.jid !== id || !box) return;
        var n = (ECO_BY[x.eco].nodes || []).filter(function (q) { return q.id === x.node; })[0];
        if (!n || !n.desc) return;
        box.textContent = n.desc.split(/(?<=[.!?])\s+/)[0];
      });
    });
  }
  function jPhotos() {
    var c = M.jid && jbyId(M.jid); if (!c) return;
    var m = document.getElementById("xi-" + c.id), t = document.getElementById("jp-main");
    if (m && t && m.querySelector("img")) t.innerHTML = m.innerHTML;
    jRelated(c).forEach(function (o) { var s = document.getElementById("xi-" + o.id), b = document.getElementById("jm-" + o.id); if (s && b && s.querySelector("img")) b.innerHTML = s.innerHTML; });
    jEnds(c).forEach(function (x, i) { var s = cimg(x.eco), b = document.getElementById("jp-e" + i); if (s && b && s.querySelector("img")) b.innerHTML = s.innerHTML; });
    
    var seen = {}, lines = [c.imgwiki].concat(jEnds(c).map(function (x) { return x.e.imgwiki; })).map(function (w) { return w && PHOTOS[w]; }).filter(function (ph) { if (!ph || seen[ph.src]) return false; seen[ph.src] = 1; return true; });
    fillPhotos("jcredit", lines.map(creditHTML));
  }
  function jFly(c, pts) {
    var dot = document.getElementById("jdot"); if (!dot) return;
    var round = c.type === "species", dur = reduce ? 1 : round ? 5200 : 3200, t0 = null, id = ++M.jfly;
    function at(u) { var f = u * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(f)), r = f - i; return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r]; }
    function step(ts) {
      if (id !== M.jfly) return;
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / dur), h = round ? (k < 0.5 ? k * 2 : 2 - k * 2) : k, u = h * h * (3 - 2 * h), q = at(u);
      dot.setAttribute("cx", q[0].toFixed(1)); dot.setAttribute("cy", q[1].toFixed(1));
      var em = document.getElementById("jemo"); if (em) { em.setAttribute("x", q[0].toFixed(1)); em.setAttribute("y", (q[1] + 1).toFixed(1)); }
      if (k < 1) requestAnimationFrame(step); else M.jdone = (M.jdone || 0) + 1;
    }
    requestAnimationFrame(step);
  }
  function showJourney(id, from) {
    var c = jbyId(id); if (!c) return;
    if (!window.d3) { withD3(function (ok) { if (ok) showJourney(id, from); }); return; }   /* the journey map is drawn with D3: wait for the library */
    var sb = document.getElementById("sbody"); if (el.webview.hidden && !el.mapview.hidden && sb) M.jScroll = sb.scrollTop;
    M.loading = null; sim.stop(); M.jid = id; M.cameFrom = null; M.jfly = (M.jfly || 0) + 1; PV.hidden = true; M.pid = null;
    el.mapview.hidden = true; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true;
    JV.hidden = false; var rt = jRouteSVG(c); M.jpts = rt.pts;
    JV.innerHTML = jHTML(c, rt); JV.scrollTop = 0; window.scrollTo(0, 0);
    jPhotos(); jRoles(c); syncHash(); jSat(rt.tiles, id);
    withSpeciesPhotos(loadJourneyPhotos);
  }
  // try one tile first: if the imagery is unreachable nothing else is requested and the plain map stays
  function jSat(tiles, id) {
    var m = tiles.match(/href="([^"]+)"/); if (!m) return;
    var im = new Image(); im.onload = function () {
      var g = M.jid === id && JV.querySelector(".jtiles"); if (g) g.innerHTML = tiles;
    }; im.src = m[1];
  }
  function closeJourney() {
    var id = M.jid; M.jfly++; M.jid = null; JV.hidden = true; showMap(); setTab("journeys");
    var sb = document.getElementById("sbody"); if (sb && M.jScroll) sb.scrollTop = M.jScroll;
    var c = document.getElementById("xc-" + id); if (c) { c.classList.add("hl"); setTimeout(function () { c.classList.remove("hl"); }, 1600); }
  }
  JV.addEventListener("load", function (ev) { var t = ev.target; if (t && t.classList && t.classList.contains("jt")) { t.setAttribute("opacity", "1"); var m = t.closest(".jmap"); if (m) m.classList.add("sat"); } }, true);
  JV.addEventListener("error", function (ev) { var t = ev.target; if (t && t.classList && t.classList.contains("jt") && t.parentNode) t.parentNode.removeChild(t); }, true);
  JV.addEventListener("keydown", function (ev) { var t = ev.target; if ((ev.key === "Enter" || ev.key === " ") && t.getAttribute && t.getAttribute("role") === "button") { ev.preventDefault(); t.click(); } });
  JV.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-jback],[data-jopen],[data-jj],#jfly"); if (!t) return;
    var c = M.jid && jbyId(M.jid);
    if (t.hasAttribute("data-jback")) closeJourney();
    else if (t.hasAttribute("data-jj")) showJourney(t.getAttribute("data-jj"));
    else if (t.hasAttribute("data-jopen")) { var p = t.getAttribute("data-jopen").split(":"); JV.hidden = true; var from = M.jid; M.jid = null; showWeb(p[0], function () { select(p[1]); }, from); }
    else if (t.id === "jfly" && c) jFly(c, M.jpts);
  });

