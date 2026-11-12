  /* ---------- Photos: only approved photos from the stored manifests are shown. ---------- */
  var PHOTOS = {};
  function esc(u) { return String(u).replace(/"/g, "%22").replace(/</g, "%3C"); }
  function escH(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function photoAttrs(p, mode) {
    return ' data-photo-key="' + encodeURIComponent(p.key) + '" data-photo-url="' + encodeURIComponent(p.src) + '" data-photo-index="0" onerror="photoFallback(this,\'' + (mode || "remove") + '\')"';
  }
  function bindPhoto(img, p, mode) {
    img.setAttribute("data-photo-key", encodeURIComponent(p.key));
    img.setAttribute("data-photo-url", encodeURIComponent(p.src));
    img.setAttribute("data-photo-index", "0");
    img.onerror = function () { photoFallback(img, mode || "remove"); };
  }
  function photoFallback(img, mode) {
    var key = img.getAttribute("data-photo-key") || "", p;
    try { key = decodeURIComponent(key); } catch (e) {}
    p = PHOTOS[key];
    if (p && p.candidates) {
      var index = parseInt(img.getAttribute("data-photo-index") || "0", 10), attempted = {}, currentUrl = img.getAttribute("data-photo-url") || "";
      try { currentUrl = decodeURIComponent(currentUrl); } catch (e) {}
      var actualIndex = p.candidates.findIndex(function (c) { return c.assetUrl === currentUrl; });
      if (actualIndex >= 0) index = actualIndex;
      p.candidates.slice(0, index + 1).forEach(function (c) { attempted[c.assetUrl] = true; });
      var next = PhotoRegistry.nextCandidate(p.candidates, index, attempted);
      if (next) {
        img.setAttribute("data-photo-index", next.index);
        img.setAttribute("data-photo-url", encodeURIComponent(next.url));
        if (img.namespaceURI === "http://www.w3.org/2000/svg") img.setAttribute("href", next.url);
        else img.src = next.url;
        return true;
      }
    }
    if (mode === "parent" && img.parentNode) img.parentNode.remove();
    else if (mode === "art" && img.parentNode) { img.parentNode.classList.remove("hasph"); img.remove(); }
    else img.remove();
    return false;
  }
  window.photoFallback = photoFallback;
  function creditHTML(p) {
    var c = p.credit;
    if (!c) return 'Photo: Wikipedia \u00B7 <a href="' + esc(p.page) + '" target="_blank" rel="noopener">article</a>';
    var a = /^unknown(\s+author)?$/i.test(c.a.trim()) ? "author unknown" : c.a.length > 46 ? c.a.slice(0, 44) + "\u2026" : c.a;
    return "Photo: " + escH(a) + " \u00B7 " + (c.lu ? '<a href="' + esc(c.lu) + '" target="_blank" rel="noopener">' + escH(c.l) + "</a>" : escH(c.l)) +
      ' \u00B7 <a href="' + esc(c.p) + '" target="_blank" rel="noopener">' + (c.s || "Wikimedia Commons") + "</a>";
  }
  function photoOf(n) { return (n.wiki && PHOTOS[n.wiki]) || (n.canonicalWiki && PHOTOS[n.canonicalWiki]) || (n.latin && PHOTOS[n.latin]) || null; }
  function shot(n) {
    var p = photoOf(n);
    if (!p) return "";
    return '<figure class="shot"><img src="' + esc(p.src) + '" alt="' + n.name + '" referrerpolicy="no-referrer"' + photoAttrs(p, "parent") + '>' +
      '<figcaption>Photo via Wikipedia · <a href="' + esc(p.page) + '" target="_blank" rel="noopener">read the article</a></figcaption></figure>';
  }
  var relayoutTimer;
  function relayoutSoon() {
    clearTimeout(relayoutTimer);
    relayoutTimer = setTimeout(function () { configure(); pendingFit = !userMoved; sim.alpha(0.35).restart(); }, 300);
  }
  function ecoPhoto(e) {
    var p = PHOTOS[e.imgwiki], box = e.li && e.li.querySelector(".cimg");
    if (!p || !box) return;
    box.innerHTML = '<img src="' + esc(p.src) + '" alt="" referrerpolicy="no-referrer" loading="lazy"' + photoAttrs(p, "remove") + '>';
    var im = box.querySelector("img");
    im.onerror = function () { if (!photoFallback(im, "remove")) box.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[e.icon] || "") + "</svg>"; };
    var pk = document.getElementById("cp-" + e.id); if (pk) pk.innerHTML = box.innerHTML;
    if (ECO === e && !state.sel && !el.webview.hidden) renderPanel();
    if (M.pid === e.id) pPhoto();
    pnlPhotos();
    if (M.jid) jPhotos();
  }
  function linkPhoto(c, refresh) {
    var p = PHOTOS[c.imgwiki], box = document.getElementById("xi-" + c.id);
    if (!p || !box || box.querySelector("img")) return;
    box.innerHTML = '<img src="' + esc(p.src) + '" alt="" referrerpolicy="no-referrer" loading="lazy"' + photoAttrs(p, "remove") + '>';
    var im = box.querySelector("img");
    im.onerror = function () { if (!photoFallback(im, "remove")) box.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[ECO_BY[ecoEnds(c)[0].eco].icon] || "") + "</svg>"; };
    if (refresh !== false && M.jid) jPhotos();
  }
  function loadJourneyPhotos() {
    CROSS.forEach(function (c) { linkPhoto(c, false); });
    if (M.jid) jPhotos();
  }
  function showPhoto(n) {
    if (n.isPage) { pShow(n); return; }
    if (n.isEco) { ecoPhoto(n.e); return; }
    if (n.isLink) { linkPhoto(n.c); return; }
    if (BY[n.id] === n) pnlPhotos();
    if (BY[n.id] !== n || n.photoShown || !photoOf(n)) return;
    n.photoShown = true;
    n.r = n.r0 * 1.3;
    var g = node.filter(function (d) { return d === n; });
    g.select(".hit").attr("r", n.r + 8);
    g.select("circle.core").attr("r", n.r);
    g.select("rect.core").attr("x", -n.r).attr("y", -n.r).attr("width", 2 * n.r).attr("height", 2 * n.r);
    g.select(".ring").attr("r", n.r + 5);
    g.select(".label").attr("y", n.r + 13);
    g.select(".glyph").style("display", "none");
    d3.select("#clip-" + n.id + " circle").attr("r", n.r - 1.8);
    g.select(".body").append("image").attr("class", "photo").attr("href", photoOf(n).src)
      .attr("data-photo-key", encodeURIComponent(photoOf(n).key)).attr("data-photo-url", encodeURIComponent(photoOf(n).src)).attr("data-photo-index", "0")
      .attr("x", -n.r).attr("y", -n.r).attr("width", 2 * n.r).attr("height", 2 * n.r)
      .attr("preserveAspectRatio", "xMidYMin slice").attr("clip-path", "url(#clip-" + n.id + ")")
      .attr("loading", "lazy").on("error", function () {
        if (!photoFallback(this, "remove")) {
          d3.select(this).remove();
          g.select(".glyph").style("display", null);
          n.photoShown = false;
        }
      });
    if (state.sel === n.id) renderPanel();
    paint();
    relayoutSoon();
  }
  /* Species pictures are our own hosted copies (photos/species-md/<file>.webp, 192 px). A place brings the entries for its own species; the journey and related-place
     views read api/species-pictures.json (every hosted picture's entry and credit). There is no fallback to another site: a species without a hosted copy shows the placeholder. */
  var SPX = null, SPX_WAIT = [];
  PhotoRegistry.setSpeciesBase(location.pathname.replace(/[^\/]*$/, "").replace(/(pilot|preview\/[^\/]+)\/$/, "") + "photos/species-md/");
  function withSpeciesPhotos(done) {
    if (!window.fetch) return;
    if (SPX === true) { done(); return; }
    SPX_WAIT.push(done);
    if (SPX !== null) return;
    SPX = false;
    Data.pictures().catch(function (e) { console.warn("Could not load species-pictures.json", e); return {}; }).then(function (all) {
      var m = all.ph || {}, credits = all.phm || {};
      Object.keys(m).forEach(function (t) {
        var candidate = PhotoRegistry.speciesCandidate(m[t], m[t] && m[t][1], 1, credits[t]);
        if (candidate) PhotoRegistry.register(PHOTOS, t, candidate);
      });
      CROSS.forEach(function (c) { if (c.imgwiki && PHOTOS[c.imgwiki]) linkPhoto(c); });
      SPX = true;
      var waiting = SPX_WAIT; SPX_WAIT = []; waiting.forEach(function (f) { f(); });
      if (M.jid) jPhotos();
    });
  }
  function loadPhotos() {
    if (ECO && ECO.phLocal) { NODES.forEach(function (n) { if (photoOf(n)) showPhoto(n); }); return; }   /* the place carries its own picture entries */
    withSpeciesPhotos(function () {
      NODES.forEach(function (n) {
        if (photoOf(n)) showPhoto(n);
      });
    });
  }

