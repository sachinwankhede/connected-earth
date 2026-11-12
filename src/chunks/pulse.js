/* The attention pulse (#689, DESIGN.md "Attention pulse"): one quiet ripple, once, from a well-connected place near the centre of the first view.
   Loaded by the page a moment after the map has settled; not part of the first view. It reaches the page only through A:
   A.map (the map), A.eco (the places), A.touched() (true once the person has pressed, typed or moved the map). */
(window.__chunk = window.__chunk || {}).pulse = function (A) {
  /* the place to pulse: of the places inside the middle half of the view, the one with the most links (idx.nr); null when there is none */
  function pick(places, box) {
    var best = null;
    places.forEach(function (e) {
      if (e.lon == null || e.lat == null || !e.idx) return;
      var x = (e.lon - box.cx) / box.w, y = (e.lat - box.cy) / box.h;
      if (Math.abs(x) > 0.25 || Math.abs(y) > 0.25) return;
      if (!best || e.idx.nr > best.idx.nr) best = e;
    });
    return best;
  }
  function run() {
    var m = A.map; if (!m || m.isMoving() || A.touched()) return;
    var b = m.getBounds(), c = m.getCenter(), e = pick(A.eco(), { cx: c.lng, cy: c.lat, w: b.getEast() - b.getWest(), h: b.getNorth() - b.getSouth() });
    if (!e) return;
    var p = m.project([e.lon, e.lat]), host = m.getContainer(), st = document.createElement("style"), r = document.createElement("i");
    st.textContent = "@keyframes ce-pulse{from{transform:translate(-50%,-50%) scale(.3);opacity:.7}to{transform:translate(-50%,-50%) scale(1.6);opacity:0}}.ce-pulse{position:absolute;width:64px;height:64px;border:2px solid #fff;border-radius:50%;pointer-events:none;z-index:2;animation:ce-pulse 1.4s ease-out 1 forwards}";
    r.className = "ce-pulse"; r.style.left = p.x + "px"; r.style.top = p.y + "px"; r.setAttribute("aria-hidden", "true");
    document.head.appendChild(st); host.appendChild(r);
    var done = function () { r.remove(); m.off("movestart", done); };
    m.on("movestart", done); r.addEventListener("animationend", done);
  }
  run.pick = pick;
  return run;
};
