  /* ---------- Current ecosystem and state ---------- */
  var NODES = [], EDGES = [], BY = {}, adj = { ins: {}, outs: {} }, ECO = null;
  var PH = !!(window.matchMedia && matchMedia("(max-width: 700px)").matches);
  function labLines(s) {
    var max = 13, w = s.split(" "), ls = [], cur = "";
    w.forEach(function (x) { if (cur && (cur + " " + x).length > max) { ls.push(cur); cur = x; } else cur = cur ? cur + " " + x : x; });
    if (cur) ls.push(cur);
    if (ls.length > 2) { ls = [ls[0], ls.slice(1).join(" ")]; }
    return ls.map(function (l) { return l.length > 15 ? l.slice(0, 14).replace(/\s+$/, "") + "…" : l; });
  }
  function sname(s) { return PH && s.length > 15 ? s.slice(0, 14).replace(/\s+$/, "") + "\u2026" : s; }
  var state = { eco: null, mode: "layers", sel: null, hov: null, trace: false, env: true, edits: {}, fx: {} };

  function isVis(n) { return state.env || !n.cat; }
  function visE(e) { return isVis(BY[e.s]) && isVis(BY[e.t]); }
  function INS(id) { return adj.ins[id].filter(visE); }
  function OUTS(id) { return adj.outs[id].filter(visE); }
  function colorVar(n) { return n.cat === "abiotic" ? "var(--tl0)" : n.cat === "decomp" ? "var(--dec)" : "var(--tl" + n.tl + ")"; }
  function kindText(n) { return n.cat === "abiotic" ? "Environment" : n.cat === "decomp" ? "Decomposer" : TL[n.tl].short; }
  function vrad(n) { return n.r * (n.k || 1); }

  var el = {
    h1: document.getElementById("h1"), stats: document.getElementById("stats"), back: document.getElementById("back"),
    webctl: document.getElementById("webctl"), eco: document.getElementById("eco"), reset: document.getElementById("reset"),
    mapview: document.getElementById("mapview"), webview: document.getElementById("webview"), legend: document.getElementById("legend")
  };
  var stage = document.getElementById("stage");
  var panel = document.getElementById("panel");
  var svg;   /* the diagram library (D3) is its own file, loaded when a food web or journey map is first needed: see initWeb() */
  var W = 1120, H = 560, PAD = 70, cur = null, userMoved = false, pendingFit = true;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function updateStats() {
    var sp = NODES.filter(function (n) { return !n.cat; }).length;
    el.stats.textContent = ECO.place + " · " + sp + " species" + (state.env ? " + environment" : "") + " · " + EDGES.filter(visE).length + " links";
  }
  function dims() {
    var cw = stage.clientWidth || 900, ch = stage.clientHeight || 560;
    if (cw < 560) ch -= 30;   /* the one-line caption under the graph */
    if (cw < 560 && state.mode === "layers") { W = Math.max(cw, 450); H = Math.max(state.env ? 760 : 640, Math.round(0.97 * ch * (W + 56) / cw)); }
    else if (cw < 560) { W = cw; H = Math.max(300, ch); }
    else if (state.mode === "layers") { W = Math.max(cw, 1120); H = Math.max(ch, state.env ? 640 : 500); }
    else { W = Math.max(cw, 620); H = Math.max(ch, 460); }
  }
  function rowY(tl) { var top = 64, bot = H - 64, lo = state.env ? 0 : 1; return top + (4 - tl) / (4 - lo) * (bot - top); }

