  // ---- place page: the place first, then a calm picture of its food web, then the detail ----
  var PV = document.getElementById("pview");
  function pData(id) {
    var e = ECO_BY[id], by = {}, deg = {}, ins = {}, outs = {};
    e.nodes.forEach(function (n) { by[n.id] = n; deg[n.id] = 0; ins[n.id] = []; outs[n.id] = []; });
    e.raw.forEach(function (r) { if (by[r[0]] && by[r[1]]) { deg[r[0]]++; deg[r[1]]++; if (!r[2] || KIND[r[2]] === "eats") { outs[r[0]].push(r[1]); ins[r[1]].push(r[0]); } } });
    return { e: e, by: by, deg: deg, ins: ins, outs: outs, bio: e.nodes.filter(function (n) { return !n.cat; }) };
  }
  function pGraphSVG(d) {
    var W = Math.max(300, Math.min(720, (PV.clientWidth || 640))), H = Math.round(W < 500 ? W * 1.02 : W * 0.62), padX = 22, padT = 22, padB = 80;
    var rows = [4, 3, 2, 1].map(function (tl) { return d.bio.filter(function (n) { return n.tl === tl; }).sort(function (a, b) { return d.deg[b.id] - d.deg[a.id]; }); }).filter(function (r) { return r.length; });
    var pos = {}, ry = function (i) { return rows.length > 1 ? padT + i * (H - padT - padB) / (rows.length - 1) : H / 2; };
    function space(r, i) { r.forEach(function (n, j) { pos[n.id] = [padX + (j + 0.5) * (W - 2 * padX) / r.length, ry(i)]; }); }
    rows.forEach(space);
    for (var pass = 0; pass < 4; pass++) rows.forEach(function (r, i) {
      var bc = {}; r.forEach(function (n) { var nb = d.ins[n.id].concat(d.outs[n.id]).filter(function (m) { return pos[m]; }); bc[n.id] = nb.length ? nb.reduce(function (a, m) { return a + pos[m][0]; }, 0) / nb.length : pos[n.id][0]; });
      r.sort(function (a, b) { return bc[a.id] - bc[b.id]; }); space(r, i);
    });
    var edges = "";
    d.bio.forEach(function (n) { d.outs[n.id].forEach(function (t) { var a = pos[n.id], b = pos[t]; if (!a || !b) return; var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2; edges += '<path class="pe" d="M' + a[0].toFixed(1) + " " + a[1].toFixed(1) + "Q" + (mx + (b[1] - a[1]) * 0.08).toFixed(1) + " " + my.toFixed(1) + " " + b[0].toFixed(1) + " " + b[1].toFixed(1) + '"/>'; }); });
    var top = d.bio.slice().sort(function (a, b) { return d.deg[b.id] - d.deg[a.id]; }), labelled = {}, lastX = {}, lw = function (n) { return Math.min(16, n.name.length) * 6.2; };
    top.forEach(function (n) { if (Object.keys(labelled).length >= 9 && n.tl < 4) return; var x = pos[n.id][0], rk = n.tl, ok = true; (lastX[rk] = lastX[rk] || []).forEach(function (q) { if (Math.abs(q[0] - x) < q[1] + lw(n) / 2 + 8) ok = false; }); if (ok) { labelled[n.id] = 1; lastX[rk].push([x, lw(n) / 2]); } });
    var nodes = d.bio.map(function (n) {
      var rowN = rows.filter(function (rw) { return rw.indexOf(n) >= 0; })[0].length, r = Math.max(6, Math.min(17, 9 + 1.7 * Math.sqrt(d.deg[n.id]), (W - 2 * padX) / rowN / 2 - 1.5)), q = pos[n.id], gs = r * 1.4, lab = labelled[n.id] ? '<text text-anchor="middle" y="' + (r + 13) + '">' + escH(n.name.length > 16 ? n.name.replace(/^(African|American|Common|Greater|Great|Northern) /, "") : n.name) + "</text>" : "";
      return '<clipPath id="pcl-' + n.id + '"><circle r="' + r.toFixed(1) + '"/></clipPath><g class="pn" data-r="' + r.toFixed(1) + '" data-node="' + n.id + '" transform="translate(' + q[0].toFixed(1) + " " + q[1].toFixed(1) + ')"><circle class="core" r="' + r.toFixed(1) + '" style="fill:var(--tl' + n.tl + ')"/><g class="gl" transform="translate(' + (-gs / 2).toFixed(1) + "," + (-gs / 2).toFixed(1) + ") scale(" + (gs / 24).toFixed(3) + ')">' + (ICONS[n.ic] || "") + "</g>" + lab + "</g>";
    }).join("");
    return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Food web of ' + escH(d.e.name) + ': ' + d.bio.length + ' species in four levels">' + edges + nodes + "</svg>";
  }
  var PNAMES = { 4: "Top predator", 3: "Hunter & scavenger", 2: "Plant-eater", 1: "Plant" };
  var PAGE_CHAINS = { yellowstone: [["aspen", "elk", "wolf"], ["willow", "beaver", "wolf"], ["grass", "elk", "lion"]] };
  function pChains(d) {
    var pick = (PAGE_CHAINS[d.e.id] || []).map(function (ids) { return ids.map(function (i) { return d.by[i]; }); }).filter(function (c) { return c.every(Boolean); });
    if (pick.length) return pick.slice(0, 2);
    var used = {}, out = [];
    d.bio.filter(function (n) { return n.tl >= 3 && d.ins[n.id].length; }).sort(function (a, b) { return b.tl - a.tl || d.deg[b.id] - d.deg[a.id]; }).forEach(function (t) {
      if (out.length >= 2) return;
      var chain = [t], c = t, g = 0;
      while (g++ < 5) {
        var pr = d.ins[c.id].map(function (i) { return d.by[i]; }).filter(function (n) { return !n.cat && n.tl < c.tl && chain.indexOf(n) < 0; }).sort(function (a, b) { return (used[a.id] ? 1 : 0) - (used[b.id] ? 1 : 0) || d.deg[b.id] - d.deg[a.id]; });
        if (!pr.length) break; chain.unshift(pr[0]); c = pr[0];
      }
      if (chain.length >= 3) { chain.forEach(function (n) { used[n.id] = 1; }); out.push(chain); }
    });
    return out;
  }
  function pLongest(d) {
    var memo = {}, vis = {};
    function f(id) { if (memo[id] != null) return memo[id]; if (vis[id]) return 0; vis[id] = 1; var m = 0; d.outs[id].forEach(function (t) { m = Math.max(m, 1 + f(t)); }); vis[id] = 0; return (memo[id] = m); }
    return d.bio.reduce(function (a, n) { return Math.max(a, f(n.id)); }, 0) + 1;
  }
  function pph(n, icons) { return '<span class="pph" data-pid="' + n.id + '" style="--c:' + colorVar(n) + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[n.ic] || "") + "</svg></span>"; }
  function pHTML(id) {
    var d = pData(id), e = d.e, byDeg = d.bio.slice().sort(function (a, b) { return d.deg[b.id] - d.deg[a.id]; });
    var plural = { 4: "Top predators", 3: "Hunters & scavengers", 2: "Plant-eaters", 1: "Plants" }, star = byDeg[0] && byDeg[0].id;
    var card = function (n) { return '<button type="button" class="pmc" data-pnode="' + n.id + '"><span class="pbox">' + pph(n) + "</span><b>" + escH(n.name) + "</b>" + (n.id === star ? '<em class="pbadge">Most connected</em>' : "") + "</button>"; };
    var rows = [4, 3, 2, 1].map(function (tl) {
      var g = byDeg.filter(function (n) { return n.tl === tl; });
      return g.length ? "<h3>" + plural[tl] + " · " + g.length + '</h3><div class="prow">' + g.map(card).join("") + "</div>" : "";
    }).join("");
    var env = e.nodes.filter(function (n) { return n.cat; });
    var eh = env.length ? "<h3>Environment · " + env.length + '</h3><div class="prow">' + env.map(card).join("") + "</div>" : "";
    var near = relatedFor(e, 10);
    var sh = near.length ? "<h3>Shares species with</h3>" + '<div class="prow">' + near.map(function (x, i) {
      return '<button type="button" class="pmc ppc" data-ppage="' + x.e.id + '"><span class="pbox"><span class="pph" data-pid="e-' + x.e.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[x.e.icon] || "") + "</svg></span>" + "</span><b>" + escH(x.e.short) + "</b><small>" + x.c + " species in common</small>" + (i === 0 ? '<em class="pbadge">Shares the most</em>' : "") + "</button>";
    }).join("") + "</div>" : "";
    var js = CROSS.filter(function (c) { return jEnds(c).some(function (x) { return x.eco === id; }); });
    var jh = js.length ? "<h3>Journeys through here</h3>" + '<div class="pjs">' + js.map(function (c) {
      var oe = jEnds(c); return '<button type="button" class="pj" data-pjourney="' + c.id + '"><span class="pph" data-pid="j-' + c.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[oe[0].e.icon] || "") + '</svg></span><span class="pjt"><i>' + escH(oe[0].e.short) + " → " + escH(oe[oe.length - 1].e.short) + "</i><b>" + escH(c.title) + '</b></span><span class="pjgo" aria-hidden="true">›</span></button>';
    }).join("") + "</div>" : "";
    var chains = pChains(d), ch = chains.length ? "<h3>Who feeds whom</h3>" + chains.map(function (c) {
      return '<div class="pchain">' + c.map(function (n, i) { return (i ? '<span class="parr" aria-hidden="true">→</span>' : "") + '<button type="button" class="pcn" data-pnode="' + n.id + '">' + pph(n) + "<small>" + escH(n.name) + "</small></button>"; }).join("") + "</div>";
    }).join("") + '<p class="fine">Each one feeds the next.</p>' : "";
    var icon = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[e.icon] || "") + "</svg>";
    return '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">‹ Places</button>' + shareBtn() + '</div>' +
      '<div class="jhero"><span class="jhimg" id="pp-main">' + icon + '</span><div><p class="jkind">' + escH(e.kind || "Place") + "</p><h2>" + escH(e.name) + '</h2><p class="jr">' + escH(e.place || "") + "</p></div></div>" +
      '<div class="jmap pmap" id="pgraph" role="button" tabindex="0" aria-label="Explore the food web of ' + escH(e.name) + '">' + pGraphSVG(d) + '<span class="jplay"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>Explore the food web</span></div>' +
      '<p class="fine">' + d.bio.length + " species. Lines run from food to eater.</p>" +
      (e.story ? '<p class="pstory"><b>The story.</b> ' + escH(e.story) + "</p>" : e.summary ? '<p class="pstory">' + escH(e.summary) + "</p>" : e.blurb ? '<p class="pstory">' + escH(e.blurb) + "</p>" : "") +
      (e.matters ? '<p class="jwhy"><b>Why it matters.</b> ' + escH(e.matters) + "</p>" : "") +
      rows + eh + ch + jh + sh +
      footHTML({ sources: e.sources, notes: e.notes, photoId: "pcredit" }) + "</article>";
  }
  function pWant(n) {
    if (!n.wiki && !n.latin) return;
    if (photoOf(n)) { pShow(n); return; }
    var pe = ECO_BY[n.eco]; if (pe && pe.phLocal && !/^[ej]-/.test(n.id)) return;   /* the place carries its own entries: a species without one has no picture */
    withSpeciesPhotos(function () { if (photoOf(n)) pShow(n); });
  }
  function pShow(n) {
    var ph = photoOf(n); if (!ph || (M.pid !== n.eco && M.sid !== n.eco)) return;
    PV.querySelectorAll('.pph[data-pid="' + n.id + '"]').forEach(function (b) {
      if (b.querySelector("img")) return;
      var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; im.loading = "lazy"; bindPhoto(im, ph); im.src = ph.src; b.appendChild(im); b.classList.add("has");
    });
    PV.querySelectorAll('.pn[data-node="' + n.id + '"]').forEach(function (g) {
      if (g.querySelector("image")) return;
      var r = +g.getAttribute("data-r"), NS = "http://www.w3.org/2000/svg", im = document.createElementNS(NS, "image");
      im.setAttribute("href", ph.src); im.setAttribute("data-photo-key", encodeURIComponent(ph.key)); im.setAttribute("data-photo-url", encodeURIComponent(ph.src)); im.setAttribute("data-photo-index", "0"); im.setAttribute("loading", "lazy"); im.setAttribute("x", -r); im.setAttribute("y", -r); im.setAttribute("width", 2 * r); im.setAttribute("height", 2 * r);
      im.setAttribute("preserveAspectRatio", "xMidYMin slice"); im.setAttribute("clip-path", "url(#pcl-" + n.id + ")");
      im.addEventListener("error", function () { if (!photoFallback(im, "remove")) g.classList.remove("ph"); });
      var gl = g.querySelector(".gl"); g.insertBefore(im, gl); g.classList.add("ph");
    });
  }
  function showPlace(id, from) {
    if (notYet(id, function () { showPlace(id, from); })) return;
    if (!ECO_BY[id]) return;
    if (FL.q && !M.pid && !M.jid && !M.fromHash) M.pushNext = true;
    M.loading = id; M.jid = null; M.sid = null; M.pid = id; M.cameFrom = from || null;
    el.mapview.hidden = true; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true; JV.hidden = true;
    PV.hidden = false; PV.innerHTML = '<article class="jp"><div class="jtop"><button type="button" class="jback" data-pback="1">‹ Places</button></div><p class="fine" style="margin-top:20px">Loading…</p></article>';
    PV.scrollTop = 0; window.scrollTo(0, 0); syncHash();
    fetchWeb(id).then(function (ok) {
      if (M.pid !== id) return;
      M.loading = null;
      if (!ok) { PV.querySelector(".fine").textContent = "This place could not be loaded. Check your connection and try again."; return; }
      PV.innerHTML = pHTML(id); PV.scrollTop = 0; pPhoto(); requestAnimationFrame(function () { rowHints(PV); });
      ECO_BY[id].nodes.forEach(function (n) { if (n.wiki || n.latin) pWant({ isPage: true, eco: id, id: n.id, wiki: n.wiki, canonicalWiki: n.canonicalWiki, latin: n.latin }); });
      PV.querySelectorAll(".pph[data-pid^='e-'],.pph[data-pid^='j-']").forEach(function (b) {
        var k = b.getAttribute("data-pid"), o = k.charAt(0) === "e" ? ECO_BY[k.slice(2)] : jbyId(k.slice(2)), w = o && o.imgwiki;
        if (w && k.charAt(0) === "e" && !o.li) makeCard(o);   /* a related place's picture is registered when its card is built, and cards are built on demand now */
        if (w) pWant({ isPage: true, eco: id, id: k, wiki: w });
      });
    });
  }
  function pPhoto() {
    var id = M.pid, m = document.getElementById("pp-main"), c = id && cimg(id);
    if (m && c && c.querySelector("img")) m.innerHTML = c.innerHTML;
    var ph = ECO_BY[id] && PHOTOS[ECO_BY[id].imgwiki], l = [];
    if (ph && m && m.querySelector("img")) l.push(creditHTML(ph));
    l.push("Species photos: Wikipedia");
    fillPhotos("pcredit", l);
  }
  function closePlace() {
    if (history.state && history.state.sp && M.pid) { history.back(); return; }   /* a place opened from a search is its own history entry: leaving it is Back, so the entries do not pile up (#412); the address change closes the page */
    M.pid = null; PV.hidden = true; showMap();
  }
  PV.addEventListener("keydown", function (ev) { var t = ev.target; if ((ev.key === "Enter" || ev.key === " ") && t.getAttribute && t.getAttribute("role") === "button") { ev.preventDefault(); t.click(); } });
  PV.addEventListener("click", function (ev) {
    var id = M.pid; if (!id) return;
    var t = ev.target.closest("[data-pback],[data-pnode],[data-pjourney],[data-ppage],#pgraph"); if (!t) return;
    if (t.hasAttribute("data-pback")) closePlace();
    else if (t.hasAttribute("data-pjourney")) { var jid = t.getAttribute("data-pjourney"); PV.hidden = true; M.pid = null; showJourney(jid); }
    else if (t.hasAttribute("data-ppage")) showPlace(t.getAttribute("data-ppage"));
    else if (t.hasAttribute("data-pnode")) { var nid = t.getAttribute("data-pnode"); PV.hidden = true; M.pid = null; showWeb(id, function () { select(nid); }, null, id); }
    else { var pn = ev.target.closest(".pn"), nd = pn && pn.getAttribute("data-node"); PV.hidden = true; M.pid = null; showWeb(id, nd ? function () { select(nd); } : null, null, id); }
  });
  function jump(eco, nodeId) { showWeb(eco, function () { select(nodeId); }); }
  /* open a place on a species by its Latin name (the page no longer carries node ids for every place's species) */
  function jumpSp(eco, latin) { showWeb(eco, function () { var n = NODES.filter(function (q) { return q.latin === latin; })[0]; if (n) select(n.id); }); }
  function showMap() {
    M.loading = null; sim.stop(); PV.hidden = true; M.pid = null; M.sid = null; M.cameFromP = null;
    el.mapview.hidden = false; el.webview.hidden = true; el.legend.hidden = true; el.webctl.hidden = true; el.back.hidden = true;
    JV.hidden = true; M.jid = null; M.cameFrom = null; el.back.innerHTML = "&larr; Places";
    el.h1.textContent = "Connected Earth";
    if (M.map) { var mc = M.map.getContainer(), rk = mc.clientWidth + "x" + mc.clientHeight; if (M.rk !== rk) { M.rk = rk; M.map.resize(); } }   /* resizing the map canvas is costly: only when the size really changed */
    renderView(false);   /* renderView already refreshes the map's connection lines (pushTies); the separate refresh that ran here repeated that work on every back tap */
    syncHash();
  }
  function setPbk() { var b = document.getElementById("pbk"); if (b) b.innerHTML = el.back.innerHTML.replace(/^\s*(&larr;|\u2190)\s*/, "\u2039 "); }
  function showWeb(id, then, fromJ, fromP) {
    if (notYet(id, function () { showWeb(id, then, fromJ, fromP); })) return;
    PV.hidden = true; M.pid = null; M.sid = null; M.cameFromP = fromP || null;
    el.mapview.hidden = true; el.webview.hidden = false; el.legend.hidden = false; el.webctl.hidden = false; el.back.hidden = false;
    JV.hidden = true; M.jid = null; M.cameFrom = fromJ || null; el.back.innerHTML = "&larr; " + (fromJ ? "Journey" : escH(ECO_BY[id].name)); setPbk();
    el.eco.value = id; M.loading = id;
    var wl = document.getElementById("webload"), ready = !!ECO_BY[id].nodes;
    wl.hidden = ready; wl.textContent = "Loading\u2026"; wl.classList.remove("err");
    fetchWeb(id).then(function (ok) {
      if (M.loading !== id) return;
      if (!ok) { wl.hidden = false; wl.textContent = "This place could not be loaded. Check your connection and try again."; wl.classList.add("err"); return; }
      if (!window.d3) { wl.hidden = false; wl.textContent = "Loading\u2026"; }
      withD3(function (okd) {
        if (M.loading !== id) return;
        if (!okd) { wl.hidden = false; wl.textContent = "This place could not be loaded. Check your connection and try again."; wl.classList.add("err"); return; }
        M.loading = null; wl.hidden = true;
        loadEco(id); syncHash(); if (then) then();
      });
    });
    syncHash();
  }
  el.back.addEventListener("click", function () { M.loading = null; var f = M.cameFrom; if (f && !el.webview.hidden) { M.cameFrom = null; showJourney(f); } else if (!el.webview.hidden && el.eco.value) showPlace(el.eco.value); else showMap(); });

