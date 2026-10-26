# local-parks toggle (national by default) + auto-generated tag. Same on every screen size.
def rep6(old, nw):
    global new
    assert old in new, old[:70]
    new = new.replace(old, nw, 1)

rep6('var FL = { q: "", kind: null, park: false };', 'var FL = { q: "", kind: null, park: false, local: false };')
rep6("    if (FL.park && !e.park) return false;\n", "    if (FL.park && !e.park) return false;\n    if (e.level === \"local\" && !FL.local && !FL.q) return false;\n")
# near me always includes local parks
rep6("ECOS.filter(pass).map(function (e) { return { e: e, d: dist(e) }; })", "ECOS.filter(function (e) { var l = FL.local; FL.local = true; var r = pass(e); FL.local = l; return r; }).map(function (e) { return { e: e, d: dist(e) }; })")
# chip
rep6("""document.getElementById("kinds").innerHTML = (np ? """, """var nl = ECOS.filter(function (e) { return e.level === "local"; }).length;
    document.getElementById("kinds").innerHTML = (nl ? '<button type="button" class="chip' + (FL.local ? " on" : "") + '" data-local="1" aria-pressed="' + FL.local + '">Local parks <b>' + nl + "</b></button>" : "") + (np ? """)
rep6("""      var pk = ev.target.closest("[data-park]");""", """      var lc = ev.target.closest("[data-local]");
      if (lc) { FL.local = !FL.local; view.focus = null; renderView(true); return; }
      var pk = ev.target.closest("[data-park]");""")
rep6('toggle("on", !!(FL.kind || FL.park))', 'toggle("on", !!(FL.kind || FL.park || FL.local))') if 'toggle("on", !!(FL.kind || FL.park))' in new else None
# auto tag
rep6("""(ECO.blurb ? '<p class="lead">' + ECO.blurb + "</p>" : "")""", """(ECO.auto ? '<p class="autotag">Auto-generated from public records and not checked by a person</p>' : "") + (ECO.blurb ? '<p class="lead">' + ECO.blurb + "</p>" : "")""")
css = """
.panel .autotag { display: inline-block; margin: 10px 0 0; padding: 3px 10px; border-radius: 999px; font: 500 11.5px var(--font-mono); letter-spacing: .02em; color: var(--muted); border: 1px dashed var(--line); }
"""
rep6(".me { width: 16px;", css + ".me { width: 16px;")
# counts shown to the person follow the toggle
rep6('var np = ECOS.filter(function (e) { return e.park; }).length;', 'var np = ECOS.filter(function (e) { return e.park && (FL.local || e.level !== "local"); }).length;')
rep6('var n = ECOS.filter(function (e) { return e.kind === k; }).length;', 'var n = ECOS.filter(function (e) { return e.kind === k && (FL.local || e.level !== "local"); }).length;')
rep6('? ECOS.length + " ecosystems"', '? ECOS.filter(function (e) { return FL.local || e.level !== "local"; }).length + " ecosystems"')
# auto-generated places appear once the map is zoomed in (or searched / a region is chosen), so the world view stays readable
rep6('features: ECOS.filter(inRegion).map(function (e) { return pt(e); }) }; }', 'features: ECOS.filter(function (e) { return inRegion(e) && (!e.auto || M.hiZ || FL.q || view.level !== "world"); }).map(function (e) { return pt(e); }) }; }')
rep6('m.addSource("atl-el", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });', 'm.addSource("atl-el", { type: "geojson", data: ecoFC(), cluster: true, clusterRadius: 36, clusterMaxZoom: 7 });\n    m.on("zoomend", function () { var hi = m.getZoom() >= 3.5; if (hi !== !!M.hiZ) { M.hiZ = hi; var fc = ecoFC(); m.getSource("atl-e").setData(fc); m.getSource("atl-el").setData(fc); } });')
