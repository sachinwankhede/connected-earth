  /* ---------- Panel ---------- */
  function chip(n) { return '<button type="button" class="chip" data-id="' + n.id + '"><i' + (n.cat === "abiotic" ? ' class="sq"' : "") + ' style="--c:' + colorVar(n) + '"></i>' + n.name + "</button>"; }
  function chipV(n, v) {
    return '<button type="button" class="chip" data-id="' + n.id + '"><i' + (n.cat === "abiotic" ? ' class="sq"' : "") + ' style="--c:' + colorVar(n) + '"></i>' + n.name + ' <b class="' + (v > 0 ? "up" : "down") + '">' + fmt(v) + "</b></button>";
  }
  function group(title, edges, key) {
    if (!edges.length) return "";
    return "<h3>" + title + " (" + edges.length + ")</h3><div class=\"prow\">" + edges.map(function (e) {
      var m = BY[e[key]];
      return '<button type="button" class="pmc" data-id="' + m.id + '"><span class="pbox"><span class="pph" data-nid="' + m.id + '" style="--c:' + colorVar(m) + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[m.ic] || "") + "</svg></span></span><b>" + escH(m.name) + "</b></button>";
    }).join("") + "</div>";
  }
  /* one line for the kind and the special role; when the role already says it (Keystone predator) it stands alone */
  function kindLine(n) {
    var k = kindText(n); if (!n.badge) return k;
    var last = k.toLowerCase().split(" ").pop();
    return escH(n.badge.toLowerCase().indexOf(last) >= 0 ? n.badge : k + " \u00B7 " + n.badge);
  }
  function factsHTML(ins, outs) {
    function c(l, kinds) { return l.filter(function (e) { return kinds.indexOf(e.kind) >= 0; }).length; }
    var eats = c(ins, ["eats", "scav"]), eaten = c(outs, ["eats", "scav"]), f = [];
    if (eats) f.push("Eats " + eats); if (eaten) f.push("Eaten by " + eaten);
    if (!f.length && outs.length) f.push("Feeds " + outs.length);
    return f.length ? '<p class="facts">' + f.join(" \u00B7 ") + "</p>" : "";
  }
  function rowHints(root) {
    (root || document).querySelectorAll(".prow").forEach(function (r) { r.classList.toggle("cont", r.scrollWidth > r.clientWidth + 6 && r.scrollLeft + r.clientWidth < r.scrollWidth - 6); });
  }
  document.addEventListener("scroll", function (ev) { var t = ev.target; if (t && t.classList && t.classList.contains("prow")) rowHints(t.parentNode); }, true);
  addEventListener("resize", function () { rowHints(); });
  function pnlPhotos() {
    if (!state.sel) return;
    panel.querySelectorAll(".pph[data-eid]").forEach(function (b) {
      var e = ECO_BY[b.getAttribute("data-eid")];
      if (e && e.imgwiki && !e.li) makeCard(e);   /* cards are built only when needed now: a related place shown here asks for its picture by building its card */
      var ph = e && e.imgwiki && PHOTOS[e.imgwiki];
      if (!ph || b.querySelector("img")) return;
      var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; im.loading = "lazy"; bindPhoto(im, ph); im.src = ph.src; b.appendChild(im); b.classList.add("has");
    });
    panel.querySelectorAll(".pph[data-nid]").forEach(function (b) {
      var m = BY[b.getAttribute("data-nid")], ph = m && photoOf(m);
      if (!ph || b.querySelector("img")) return;
      var im = document.createElement("img"); im.alt = ""; im.referrerPolicy = "no-referrer"; im.loading = "lazy"; bindPhoto(im, ph); im.src = ph.src; b.appendChild(im); b.classList.add("has"); b.classList.add("has");
    });
  }
  function overviewHTML() {
    var names = { 4: "Top predators", 3: "Hunters & scavengers", 2: "Plant-eaters", 1: "Plants", 0: "Environment" };
    function chip(n) { return '<button type="button" class="chip" data-id="' + n.id + '"><i' + (n.cat === "abiotic" ? ' class="sq"' : "") + ' style="--c:' + colorVar(n) + '"></i>' + n.name + "</button>"; }
    var bio = NODES.filter(function (n) { return !n.cat; });
    function deg(n) { return INS(n.id).length + OUTS(n.id).length; }
    var h = "";
    [4, 3, 2, 1].forEach(function (tl) {
      var g = bio.filter(function (n) { return n.tl === tl; }).sort(function (a, b) { return deg(b) - deg(a); });
      if (g.length) h += "<h3>" + names[tl] + " \u00b7 " + g.length + '</h3><div class="chips">' + g.map(chip).join("") + "</div>";
    });
    var near = relatedFor(ECO_BY[state.eco], 8);
    if (near.length) h += "<h3>Shares species with</h3>" + '<div class="chips">' + near.map(function (x) { return '<button type="button" class="chip" data-goto="' + x.e.id + '">' + x.e.short + " <b>" + x.c + "</b></button>"; }).join("") + "</div>";
    var env = NODES.filter(function (n) { return n.cat; });
    if (env.length) h += "<h3>Environment \u00b7 " + env.length + '</h3><div class="chips">' + env.map(chip).join("") + "</div>";
    return h;
  }
  function emptyHTML() {
    var t = ECO.tip, n = BY[t.id];
    var ph = ECO.imgwiki && PHOTOS[ECO.imgwiki] ? '<figure class="shot"><img src="' + esc(PHOTOS[ECO.imgwiki].src) + '" alt="' + ECO.name + '" referrerpolicy="no-referrer"' + photoAttrs(PHOTOS[ECO.imgwiki], "parent") + '><figcaption>' + creditHTML(PHOTOS[ECO.imgwiki]) + '</figcaption></figure>' : "";
    return '<p class="eyebrow">' + ECO.place + "</p>" + ph +
      (ECO.blurb ? '<p class="lead">' + ECO.blurb + "</p>" : "") + overviewHTML() +
      footHTML({ sources: ECO.sources, notes: ECO.notes }) +
      (ECO.notes ? '<p class="fine">' + ECO.notes + "</p>" : "");
  }
  function traceText() {
    var a = ancestors(state.sel);
    return "Traces back through " + a.size + (a.size === 1 ? " node" : " nodes") + " to " + (state.env ? "the environment." : "the producers.");
  }
  function fxHTML() {
    var pe = eff(), ids = Object.keys(pe).filter(function (id) { return BY[id] && isVis(BY[id]); });
    if (!ids.length) return '<p class="fine">Move the slider to raise or lower this population and see who else is affected.</p>';
    var x = state.fx;
    var direct = new Set();
    ids.forEach(function (id) { INS(id).concat(OUTS(id)).forEach(function (e) { direct.add(e.s); direct.add(e.t); }); });
    var others = NODES.filter(function (n) { return isVis(n) && pe[n.id] === undefined && Math.abs(x[n.id]) >= 1; })
      .sort(function (a, b) { return Math.abs(x[b.id]) - Math.abs(x[a.id]); });
    function list(arr) {
      return '<div class="chips">' + arr.map(function (n) {
        return chipV(n, x[n.id]).replace('class="chip"', 'class="chip' + (direct.has(n.id) ? "" : " ind") + '"');
      }).join("") + "</div>";
    }
    var ups = others.filter(function (n) { return x[n.id] > 0; }), downs = others.filter(function (n) { return x[n.id] < 0; });
    var quiet = NODES.filter(function (n) { return isVis(n) && pe[n.id] === undefined && Math.abs(x[n.id]) < 1; }).length;
    return "<h4>Your changes</h4><div class=\"chips\">" + ids.map(function (id) { return chipV(BY[id], pe[id]) + (state.edits[id] === undefined ? '<span class="tag">from linked ecosystem</span>' : ''); }).join("") +
      '<button type="button" class="chip" data-resetall>Reset all</button></div>' +
      "<h4>Whole ecosystem: " + others.length + " of " + (others.length + quiet) + " other nodes change</h4>" +
      '<div class="fx-list">' +
      (downs.length ? "<h4>Decrease (" + downs.length + ")</h4>" + list(downs) : "") +
      (ups.length ? "<h4>Increase (" + ups.length + ")</h4>" + list(ups) : "") +
      (quiet ? '<p class="fine">' + quiet + " nodes change by less than 1%.</p>" : "") + "</div>" +
      ids.filter(function (id) { return state.edits[id] !== undefined && BY[id].xl && BY[id].xl.dir !== "in"; }).map(function (id) {
        var o = BY[id].xl.other;
        return '<p class="fine"><b>Carries over:</b> ' + BY[id].name + ' also changes in ' + ECO_BY[o.eco].short + ' (' + fmt(pe[id] * COUPLE) + '). Open that ecosystem to see the effects there.</p>';
      }).join("") +
      '<p class="fine">Solid chips are direct neighbours. Dashed chips are knock-on effects further away. On the graph, blue rings rise and pink rings fall. A simple model: direction and rough size, not a forecast.</p>';
  }
  function whatIfHTML(n) {
    var v = state.edits[n.id] || 0;
    return '<div class="wi"><h3>What if&hellip;</h3>' +
      '<div class="wi-row"><label for="pop">Change in ' + n.name + '</label><output id="pop-out" for="pop">' + (v ? fmt(v) : "Normal") + "</output></div>" +
      '<input type="range" id="pop" min="-100" max="200" step="5" value="' + v + '">' +
      '<div class="presets"><button type="button" data-set="-100">Remove</button><button type="button" data-set="-50">−50%</button><button type="button" data-set="50">+50%</button><button type="button" data-set="100">+100%</button><button type="button" data-set="0">Normal</button></div>' +
      '<div class="fx" id="fx">' + fxHTML() + "</div></div>";
  }
  function linkHTML(n) {
    if (n.xl) {
      var o = n.xl.other, oe = ECO_BY[o.eco], on = { name: nodeName(o.eco, o.node) };
      var hd = n.xl.dir === "in" ? "Flows in from another ecosystem" : n.xl.dir === "out" ? "Flows out to another ecosystem" : "Linked ecosystem";
      return '<div class="xlink"><h3>' + hd + '</h3><p><b>' + n.xl.link.title + '.</b> ' + n.xl.link.text + '</p><button type="button" class="chip" data-jump="' + o.eco + ':' + o.node + '">Open ' + on.name + ' in ' + oe.short + ' &rarr;</button> <button type="button" class="chip" data-journey="' + n.xl.link.id + '">Read the journey</button></div>';
    }
    if (n.fl) return '<div class="xlink"><h3>Outside input</h3><p><b>' + n.fl.title + '.</b> ' + n.fl.text + '</p></div>';
    return "";
  }
  /* the same footer on every page: one collapsed "Sources & credits" section */
  // One footer for every screen. Groups always appear in this order and only when they have content:
  // Sources (links), Photos (credits), Notes (plain text), Evidence (species sheet only).
  function footGroup(h, body, id, empty) { return '<div class="fgrp"' + (id ? ' id="' + id + '"' : "") + (empty ? " hidden" : "") + "><h4>" + h + "</h4>" + body + "</div>"; }
  function footList(items) { return '<ul class="srcs">' + items.map(function (x) { return "<li>" + x + "</li>"; }).join("") + "</ul>"; }
  function footHTML(o) {
    var src = o.sources && o.sources.length ? o.sources.map(function (q) { return '<a href="' + esc(q.url || q.u) + '" target="_blank" rel="noopener noreferrer">' + (q.title || escH(q.t)) + "</a>"; }) : [];
    var ph = o.photos || [];
    return '<details class="srcd"><summary>Sources &amp; credits</summary>' +
      (src.length ? footGroup("Sources", footList(src)) : "") +
      (o.photoId ? footGroup("Photos", '<ul class="srcs"></ul>', o.photoId, true) : ph.length ? footGroup("Photos", footList(ph)) : "") +
      (o.notes ? footGroup("Notes", "<p>" + escH(o.notes) + "</p>") : "") +
      (o.evidence ? footGroup("Evidence", o.evidence) : "") + "</details>";
  }
  function fillPhotos(id, lines) { var g = document.getElementById(id); if (!g) return; var u = g.querySelector("ul"); u.innerHTML = lines.map(function (x) { return "<li>" + x + "</li>"; }).join(""); g.hidden = !lines.length; }
  function shareBtn() {
    return '<button type="button" class="ibtn shbtn" data-share="1" aria-label="Share link" title="Share"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>' +
      '<svg class="ok" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 13l4 4L19 7"/></svg></button>';
  }
  function srcLinks(list) {
    return '<ul class="srcs">' + list.map(function (s) { return '<li><a href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + s.title + '</a></li>'; }).join("") + "</ul>";
  }
  function srcList(n) {
    var list = (n.src || []).slice();
    if (n.wiki) list.push({ title: "Wikipedia: " + n.wiki, url: "https://en.wikipedia.org/wiki/" + encodeURIComponent(n.wiki.replace(/ /g, "_")) });
    return list;
  }
  var EVT = { g: "Recorded in GloBI", gg: "GloBI has records for this genus", gf: "GloBI has records for this family", ga: "Added from a GloBI record", a: "From the ecosystem sources and general ecology (no GloBI record found)" };
  function evHTML(ins, outs) {
    var ev = ECO.ev || {}, rows = [];
    ins.concat(outs).forEach(function (e) {
      if (e.kind !== "eats" && e.kind !== "scav") return;
      var x = ev[e.s + ">" + e.t]; if (!x) return;
      var link = x[1] ? ' <a href="https://api.globalbioticinteractions.org/interaction?sourceTaxon=' + encodeURIComponent(x[1]) + "&targetTaxon=" + encodeURIComponent(x[2]) + '&interactionType=eats&type=json.v2" target="_blank" rel="noopener noreferrer">view records</a>' : "";
      rows.push("<li><b>" + BY[e.s].name + " &rarr; " + BY[e.t].name + "</b><br>" + EVT[x[0]] + link + "</li>");
    });
    return rows.length ? '<details class="evd"><summary>Evidence for feeding links (' + rows.length + ")</summary><ul>" + rows.join("") + "</ul></details>" : "";
  }
  function whereHTML(n, ids) {
    var hits = ids.filter(function (i) { return i !== state.eco && ECO_BY[i]; }).map(function (i) { return { e: ECO_BY[i], lat: n.latin }; });
    if (!hits.length) return "";
    return '<h3 class="hrow"><span>Also found in ' + hits.length + (hits.length === 1 ? " other place" : " other places") + "</span>" + '<a href="#" data-spage="' + esc(n.latin) + '">Species page \u203a</a>' + '</h3><div class="prow">' + hits.slice(0, 12).map(function (h) {
      return '<button type="button" class="pmc ppc" data-jump-sp="' + h.e.id + "|" + esc(h.lat) + '"><span class="pbox"><span class="pph" data-eid="' + h.e.id + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[h.e.icon] || "") + "</svg></span></span><b>" + escH(h.e.short) + "</b><small>" + escH(h.e.place || "") + "</small></button>";
    }).join("") + "</div>";
  }
  function whereElseHTML(n) {
    if (n.cat || !n.latin) return "";
    if (SPPL.d[n.latin]) return whereHTML(n, SPPL.d[n.latin]);
    sppPlaces(n.latin).then(function (ids) {   /* the places of this species are a small file of their own: the row fills in when it arrives */
      var el = document.getElementById("where-else");
      if (el && el.getAttribute("data-latin") === n.latin && state.sel && BY[state.sel] === n) { el.outerHTML = whereHTML(n, ids); pnlPhotos(); requestAnimationFrame(function () { rowHints(panel); }); }
    });
    return '<div id="where-else" data-latin="' + esc(n.latin) + '"></div>';
  }
  var P = { set: function () {}, toggle: function () {}, last: undefined };
  function renderPanel() {
    var id = state.sel;
    var ps = document.getElementById("psheet");
    if (ps) ps.classList.toggle("nosel", !id);
    stage.classList.toggle("hasel", !!id);
    var pr = document.getElementById("prow");
    if (pr) {
      var nn = id && BY[id];
      pr.innerHTML = (nn ? (photoOf(nn) ? '<span class="sth"><img src="' + esc(photoOf(nn).src) + '" alt="" referrerpolicy="no-referrer"' + photoAttrs(photoOf(nn), "remove") + '></span>' : "") + '<span class="stx"><span class="stt">' + nn.name + '</span><span class="ssub">' + kindLine(nn) + "</span></span>" : '<span class="stt">' + ECO.name + '</span><span class="scnt">' + ECO.nodes.filter(function (n) { return !n.cat; }).length + ' species</span>');
      if (window.matchMedia && matchMedia("(max-width: 700px)").matches && P.last !== id) P.set(id && !P.keepMin ? "half" : "min");
      P.last = id;
    }
    if (!id || !BY[id]) { panel.innerHTML = emptyHTML(); return; }
    var n = BY[id], ins = INS(id), outs = OUTS(id);
    function k(list, kind) { return list.filter(function (e) { return e.kind === kind; }); }
    var hasUp = ins.some(flows);
    panel.innerHTML =
      '<button type="button" class="x" data-clear aria-label="Clear selection">&times;</button>' +
      '<div class="head"><button type="button" class="pchev" data-pchev aria-label="Collapse"></button><div class="art' + (n.cat === "abiotic" ? " sq" : "") + (photoOf(n) ? " hasph" : "") + '" style="--c:' + colorVar(n) + '">' + (photoOf(n) ? '<img src="' + esc(photoOf(n).src) + '" alt="' + escH(n.name) + '" referrerpolicy="no-referrer"' + photoAttrs(photoOf(n), "art") + '>' : "") + '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[n.ic] || "") + "</svg></div><div>" +
      '<span class="tlpill">' + kindLine(n) + "</span>" +
      "<h2>" + n.name + "</h2>" + (n.latin ? '<p class="latin">' + n.latin + "</p>" : "") + '</div></div>' +
      "<p>" + n.desc + "</p>" + aboutHTML(n) +
      group("What " + n.name + " eats", k(ins, "eats"), "s") +
      group("What eats " + n.name, k(outs, "eats"), "t") +
      group(n.name + " scavenges from", k(ins, "scav"), "s") +
      group(n.name + " depends on", k(ins, "res"), "s") +
      group(n.name + " breaks down", k(ins, "det"), "s") +
      group("Scavenged by", k(outs, "scav"), "t") +
      group(n.name + " supports", k(outs, "res"), "t") +
      group("Broken down by", k(outs, "det"), "t") +
      (hasUp ? '<label class="trace"><input type="checkbox" id="trace"' + (state.trace ? " checked" : "") + '><span>Trace back to its energy source</span></label><p class="trace-note" id="trace-note">' + (state.trace ? traceText() : "") + "</p>" : "") +
      linkHTML(n) + whereElseHTML(n) +
      footHTML({ sources: srcList(n), photos: photoOf(n) ? [creditHTML(photoOf(n))] : [], evidence: evHTML(ins, outs) }) + whatIfHTML(n);
    pnlPhotos(); requestAnimationFrame(function () { rowHints(panel); });
  }
  function setEdit(id, v) {
    if (!id) return;
    if (v === 0) delete state.edits[id]; else state.edits[id] = v;
    paint();
    var out = document.getElementById("pop-out");
    if (out) out.textContent = v ? fmt(v) : "Normal";
    var fxEl = document.getElementById("fx");
    if (fxEl) fxEl.innerHTML = fxHTML();
  }
  function clearEdits() { EDITS = {}; state.edits = EDITS[state.eco] = {}; paint(); renderPanel(); }

  panel.addEventListener("click", function (ev) {
    var pre = ev.target.closest("[data-set]");
    if (pre) {
      var val = +pre.getAttribute("data-set");
      setEdit(state.sel, val);
      var sl = document.getElementById("pop");
      if (sl) sl.value = val;
      return;
    }
    if (ev.target.closest("[data-resetall]")) { clearEdits(); return; }
    var spb = ev.target.closest("[data-spage]"); if (spb) { ev.preventDefault(); M.pushNext = true; showSpecies(sidOf({ latin: spb.getAttribute("data-spage") }), ECO_BY[state.eco] && ECO_BY[state.eco].name); return; }   /* the species page, and Back returns to this place's graph */
    var gt = ev.target.closest("[data-goto]"); if (gt) { showPlace(gt.getAttribute("data-goto")); return; }
    var jr = ev.target.closest("[data-journey]"); if (jr) { showJourney(jr.getAttribute("data-journey")); return; }
    var js = ev.target.closest("[data-jump-sp]");
    if (js) { var jq = js.getAttribute("data-jump-sp").split("|"); jumpSp(jq[0], jq[1]); return; }
    var jm = ev.target.closest("[data-jump]");
    if (jm) { var jp = jm.getAttribute("data-jump").split(":"); jump(jp[0], jp[1]); return; }
    var b = ev.target.closest("[data-id]");
    if (b) { select(b.getAttribute("data-id")); return; }
    if (ev.target.closest("[data-clear]")) clearSel();
  });
  panel.addEventListener("change", function (ev) {
    if (ev.target.id !== "trace") return;
    state.trace = ev.target.checked;
    document.getElementById("trace-note").textContent = state.trace ? traceText() : "";
    apply();
  });
  panel.addEventListener("input", function (ev) { if (ev.target.id === "pop") setEdit(state.sel, +ev.target.value); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") clearSel(); });

