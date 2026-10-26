# local-parks toggle (national by default) + auto-generated tag. Same on every screen size.
def rep6(old, nw):
    global new
    assert old in new, old[:70]
    new = new.replace(old, nw, 1)

rep6('var FL = { q: "", kind: null, park: false };', 'var FL = { q: "", kind: null, park: false, local: false };')
rep6("    if (FL.park && !e.park) return false;\n", "    if (FL.park && !e.park) return false;\n    if (e.level === \"local\" && !FL.local && !FL.q) return false;\n")
# near me always includes local parks
rep6("ECOS.filter(pass).map(function (e) { return { e: e, d: dist(e) }; })", "ECOS.filter(function (e) { var l = FL.local; FL.local = true; var r = pass(e); FL.local = l; return r; }).map(function (e) { return { e: e, d: dist(e) }; })")
# layers-panel switch (replaces the chip)
rep6("""document.getElementById("kinds").innerHTML = (np ? """, """var nl = ECOS.filter(function (e) { return e.level === "local"; }).length, lb = document.getElementById("locbtn");
    if (lb) { lb.style.display = nl ? "" : "none"; lb.setAttribute("aria-pressed", FL.local ? "true" : "false"); }
    document.getElementById("kinds").innerHTML = (np ? """)
rep6('return n ? \'<button type="button" class="chip\' + (FL.kind === k', 'return n && !(k === "Urban" && n < 5) ? \'<button type="button" class="chip\' + (FL.kind === k')
# auto tag
rep6("""(ECO.blurb ? '<p class="lead">' + ECO.blurb + "</p>" : "")""", """(ECO.auto ? '<p class="autotag">Auto-generated from public records and not checked by a person</p>' : "") + (ECO.blurb ? '<p class="lead">' + ECO.blurb + "</p>" : "")""")
css = """
.zoomc #locbtn[aria-pressed="true"] { background: var(--accent); color: #fff; }
.panel .autotag { display: inline-block; margin: 10px 0 0; padding: 3px 10px; border-radius: 999px; font: 500 11.5px var(--font-mono); letter-spacing: .02em; color: var(--muted); border: 1px dashed var(--line); }
"""
rep6(".me { width: 16px;", css + ".me { width: 16px;")
# counts shown to the person follow the toggle
rep6('var np = ECOS.filter(function (e) { return e.park; }).length;', 'var np = ECOS.filter(function (e) { return e.park && (FL.local || e.level !== "local"); }).length;')
rep6('var n = ECOS.filter(function (e) { return e.kind === k; }).length;', 'var n = ECOS.filter(function (e) { return e.kind === k && (FL.local || e.level !== "local"); }).length;')
rep6('? ECOS.length + " ecosystems"', '? ECOS.filter(function (e) { return FL.local || e.level !== "local"; }).length + " ecosystems"')
# auto-generated places appear once the map is zoomed in (or searched / a region is chosen), so the world view stays readable
rep6('features: ECOS.filter(inRegion).map(function (e) { return pt(e); }) }; }', 'features: ECOS.filter(function (e) { return inRegion(e) && (!e.auto || e.level === "local" || M.hiZ || FL.q || view.level !== "world"); }).map(function (e) { return pt(e); }) }; }')
rep6('m.addSource("atl-el", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });', 'm.addSource("atl-el", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });\n    m.on("zoomend", function () { var hi = m.getZoom() >= 3.5; if (hi !== !!M.hiZ) { M.hiZ = hi; var fc = ecoFC(); m.getSource("atl-e").setData(fc); m.getSource("atl-el").setData(fc); } });')

# Local parks: its own button in the right-hand toolbar, between layers and the world button
rep6('<button type="button" id="zin"', '<button type="button" id="locbtn" aria-pressed="false" aria-label="Local parks" title="Local parks" style="display:none"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.2"/></svg></button><button type="button" id="zin"')
rep6('document.getElementById("kinds").addEventListener("click", function (ev) {', 'document.getElementById("locbtn").addEventListener("click", function () { FL.local = !FL.local; view.focus = null; renderView(true); });\n    document.getElementById("kinds").addEventListener("click", function (ev) {')

# filters and the Local parks button keep the camera where it is; the map only moves if nothing from the new selection is in view
rep6('  function renderView(animate) {\n    var m = M.map;', '''  function filterView() {
    renderView(false);
    var m = M.map; if (!m || !M.styleReady) return;
    var bd = m.getBounds(), any = ECOS.some(function (e) { return inRegion(e) && bd.contains([e.lon, e.lat]); });
    if (!any && ECOS.some(inRegion)) mapFit(true);
  }
  function renderView(animate) {
    var m = M.map;''')
rep6('FL.park = !FL.park; view.focus = null; renderView(true); return;', 'FL.park = !FL.park; view.focus = null; filterView(); return;')
rep6('FL.kind = FL.kind === b.getAttribute("data-kind") ? null : b.getAttribute("data-kind"); view.focus = null; renderView(true);', 'FL.kind = FL.kind === b.getAttribute("data-kind") ? null : b.getAttribute("data-kind"); view.focus = null; filterView();')
rep6('FL.local = !FL.local; view.focus = null; renderView(true); });', 'FL.local = !FL.local; view.focus = null; filterView(); });')

# the hook: "N places. N species. N links." on the home screen; follows the Local parks button
rep6('  function filterView() {', '''  function heroStats() {
    var sp = {}, ns = 0, np = 0, nl = 0;
    ECOS.forEach(function (e) {
      if (e.level === "local" && !FL.local) return;
      np++;
      e.nodes.forEach(function (n) { if (!n.cat && n.latin) { var k = n.latin.toLowerCase(); if (!sp[k]) { sp[k] = 1; ns++; } } });
      e.raw.forEach(function (r) { if (r.length === 2 || r[2] === "s") nl++; });
    });
    var f = function (x) { return x.toLocaleString("en-US"); };
    return f(np) + " places. " + f(ns) + " species. " + f(nl) + " links.";
  }
  function filterView() {''')
rep6('? ECOS.filter(function (e) { return FL.local || e.level !== "local"; }).length + " ecosystems"', '? heroStats()')
rep6('var cnt = shown + (shown === 1 ? " ecosystem" : " ecosystems");', 'var cnt = shown + (shown === 1 ? " place" : " places");')
rep6('list.length + (list.length === 1 ? " ecosystem" : " ecosystems") + " in " + region;', 'list.length + (list.length === 1 ? " place" : " places") + " in " + region;')
rep6('list.length + (list.length === 1 ? " ecosystem matches " : " ecosystems match ")', 'list.length + (list.length === 1 ? " place matches " : " places match ")')

# show the hook where people will see it: first line of the home sheet / panel
rep6('<div class="sbody" id="sbody">', '<div class="sbody" id="sbody"><p class="hook" id="hook" hidden></p>')
rep6('    var sr = document.getElementById("srow");', '''    var hk = document.getElementById("hook");
    if (hk) { var home = view.level === "world" && !FL.q; hk.hidden = !home; if (home) { hk.innerHTML = heroStats().replace(/([\\d,]+) (places|species|links)\\./g, "<b>$1</b> $2."); } }
    var sr = document.getElementById("srow");''')
css2 = """
.hook { margin: 2px 0 12px; font: 500 15px/1.35 var(--font-body); color: var(--muted); }
.hook b { font: 700 18px var(--font-display); color: var(--ink); font-variant-numeric: tabular-nums; }
"""
rep6(".me { width: 16px;", css2 + ".me { width: 16px;")

# filter chips: no counts (they are not what a person decides by); the home sheet already says it once
rep6("""">Protected areas <b>' + np + "</b></button>" """.strip(), """">Protected areas</button>'""".strip())
rep6("""k + " <b>" + n + "</b></button>" """.strip(), """k + "</button>" """.strip())
rep6('var cnt = shown + (shown === 1 ? " place" : " places");', 'var cnt = view.level === "world" && !FL.q ? "" : shown + (shown === 1 ? " place" : " places");')

# five short habitat chips (no "Protected areas", no counts); a chip stands for one or more habitat types
import re as _re
_a = new.index("  function kindsHTML() {")
_b = new.index("  function tiesHTML(")
new = new[:_a] + r'''  var KGROUPS = [["Forest", ["Forest"]], ["Grass & desert", ["Grassland", "Desert"]], ["Freshwater", ["Lakes & wetlands"]], ["Ocean", ["Coast & ocean"]], ["Cold & high", ["Polar & mountain"]], ["Urban", ["Urban"]]];
  function kindsOf(label) { for (var i = 0; i < KGROUPS.length; i++) if (KGROUPS[i][0] === label) return KGROUPS[i][1]; return [label]; }
  function kindsHTML() {
    var nl = ECOS.filter(function (e) { return e.level === "local"; }).length, lb = document.getElementById("locbtn");
    if (lb) { lb.style.display = nl ? "" : "none"; lb.setAttribute("aria-pressed", FL.local ? "true" : "false"); }
    document.getElementById("kinds").innerHTML = KGROUPS.map(function (g) {
      var n = ECOS.filter(function (e) { return g[1].indexOf(e.kind) >= 0 && (FL.local || e.level !== "local"); }).length;
      if (!n || (g[0] === "Urban" && n < 5)) return "";
      return '<button type="button" class="chip' + (FL.kind === g[0] ? " on" : "") + '" data-kind="' + g[0] + '" aria-pressed="' + (FL.kind === g[0]) + '"><i class="kd" style="--kc:' + KC[g[1][0]] + '"></i>' + g[0] + "</button>";
    }).join("");
  }
''' + new[_b:]
assert "if (FL.kind && e.kind !== FL.kind) return false;" in new
new = new.replace("if (FL.kind && e.kind !== FL.kind) return false;", "if (FL.kind && kindsOf(FL.kind).indexOf(e.kind) < 0) return false;", 1)

# smaller habitat chips (phone and desktop alike)
rep6(".me { width: 16px;", """.filters .kinds .chip { min-height: 30px; padding: 3px 10px 3px 9px; font-size: 12.5px; gap: 0; }
.filters .kinds .chip i.kd { width: 8px; height: 8px; margin-right: 6px; }
.me { width: 16px;""")
