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
