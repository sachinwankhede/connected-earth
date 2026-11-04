  /* ---------- What-if model. Values are percent change from normal. A species you edit is held at that value; every other node is relaxed toward two rules until the numbers settle:
     1) bottom-up: it follows the average of its food and inputs (scavenged food counts half), damped to 80%
     2) top-down: it loses a quarter of the combined change of the animals that eat it
     This shows direction and rough size of knock-on effects. It is not a population forecast. ---------- */
  function compute() {
    var x = {}, pins = eff();
    NODES.forEach(function (n) { x[n.id] = 0; });
    function pinned(id) { return pins[id] !== undefined && BY[id] && isVis(BY[id]); }
    NODES.forEach(function (n) { if (pinned(n.id)) x[n.id] = pins[n.id]; });
    for (var it = 0; it < 80; it++) {
      var nx = {};
      NODES.forEach(function (n) {
        if (!isVis(n)) { nx[n.id] = 0; return; }
        if (pinned(n.id)) { nx[n.id] = pins[n.id]; return; }
        var up = 0, w = 0, td = 0;
        INS(n.id).forEach(function (e) { var wt = e.kind === "scav" ? 0.5 : 1; up += wt * x[e.s]; w += wt; });
        OUTS(n.id).forEach(function (e) { if (e.kind === "eats") td += x[e.t]; });
        var v = (w ? 0.8 * up / w : 0) - 0.25 * td;
        v = Math.max(-100, Math.min(300, v));
        nx[n.id] = 0.5 * x[n.id] + 0.5 * v;
      });
      x = nx;
    }
    return x;
  }
  function scaleFor(v) { return Math.max(0.4, Math.min(1.7, Math.sqrt(Math.max(0.05, 1 + v / 100)))); }
  function fmt(v) { var r = Math.round(v); return r === 0 ? "0%" : (r > 0 ? "+" : "−") + Math.abs(r) + "%"; }

  function paint() {
    if (!node) return;
    var x = compute(), pe = eff(), anyE = Object.keys(pe).some(function (k) { return BY[k] && isVis(BY[k]); });
    state.fx = x;
    node.each(function (d) {
      var vis = isVis(d), v = vis ? x[d.id] : 0, own = vis && state.edits[d.id] !== undefined, pinned = vis && pe[d.id] !== undefined;
      d.k = scaleFor(v);
      var g = d3.select(this);
      g.select(".body").style("transform", "scale(" + d.k + ")");
      g.select(".label").attr("y", d.r * d.k + 13);
      g.select(".xlb").attr("transform", "translate(" + (-d.r * d.k * 0.75) + "," + (-d.r * d.k * 0.75) + ")");
      g.classed("edited", own).classed("inh", pinned && !own).classed("gone", v <= -99)
        .classed("up", !pinned && v >= 1).classed("down", !pinned && v <= -1)
        .classed("quiet", anyE && !pinned && Math.abs(v) < 1);
      var show = Math.abs(v) >= 1;
      var dl = g.select(".delta").style("display", show ? null : "none");
      if (show) {
        var txt = v <= -99 ? "removed" : (v > 0 ? "▲ " : "▼ ") + Math.round(Math.abs(v)) + "%";
        dl.attr("transform", "translate(" + (d.r * d.k * 0.5) + "," + (-d.r * d.k - 15) + ")");
        dl.select("rect").attr("width", txt.length * 6.3 + 10).attr("class", v > 0 ? "up" : "down");
        dl.select("text").text(txt);
      }
    });
    el.reset.hidden = !Object.keys(EDITS).some(function (k) { return Object.keys(EDITS[k]).length; });
    ticked();
    if (!state.sel && !state.hov) { edge.classed("dim", false).classed("rip", function (e) { return anyE && rippleEdge(e); }); } else apply();
  }

