  /* Suggestions while typing (#413): a short dropdown under the search box. The rows come from api/search[-pilot]/s-<first two letters of the last typed word>.json
     (written by the build): places in home-list order and species with the number of places. The whole name typed comes first, then names that start with the text, then names
     with a word that starts with it; within each the better known first, places and species interleaved (#424). Every row says its type: "Place · <state or country>" (just "Place" until
     the local places have arrived) or "Species · in N places". At most 3 rows on a phone, 5 on a wider screen. A place row opens the place, a species row runs
     "Show on the map" for that species. The dropdown shows only while the box has focus and at least two letters are typed; Enter, Clear, a tap on a row or a tap
     elsewhere closes it. Nothing here blocks the normal search, which still runs on every keystroke. */
  var SUG = { bk: {}, n: 0, rows: [], q: "" };
  var sugBox = document.getElementById("sug"), sugIn = document.getElementById("q");
  var SUG_LEAF = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19c3-4 6-7 9-9"/></svg>';
  var SUG_CHEV = '<svg class="sgo" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
  function sugMax() { return window.matchMedia && matchMedia("(max-width: 700px)").matches ? 3 : 5; }
  function sugHide() { SUG.n++; SUG.rows = []; if (sugBox) { sugBox.hidden = true; sugBox.innerHTML = ""; } sugIn.setAttribute("aria-expanded", "false"); }
  /* rows for the typed text q out of one suggestion file d: every typed word must start a word of the name. Rank k: 0 the whole name (or Latin name) is what was typed, 1 the
     name starts with it, 2 only a word of the name starts with it. Within a rank the better known first: a place by its position in the home list, a species by its number of
     places; the two kinds are interleaved by that position (the best place, the best species, the second place, ...), so the type alone never decides (#424) */
  function sugPick(q, d) {
    var ws = srchWords(q), phrase = ws.join(" "), P = [], S = [];
    if (!ws.length) return [];
    function words(label) { return srchWords(label); }
    function has(lw) { return ws.every(function (w) { return lw.some(function (x) { return x.lastIndexOf(w, 0) === 0; }); }); }
    function rank(names) { var r = 2; names.forEach(function (n) { r = Math.min(r, n === phrase ? 0 : n.lastIndexOf(phrase, 0) === 0 ? 1 : 2); }); return r; }
    (d.p || []).forEach(function (r, i) { var nm = words(r[1]); if (has(nm)) P.push({ t: "p", id: r[0], name: r[1], k: rank([nm.join(" ")]), i: i }); });
    (d.s || []).forEach(function (r, i) { var nm = words(r[1]), lt = words(r[0]); if (has(nm.concat(lt))) S.push({ t: "s", latin: r[0], name: r[1], n: r[2], k: rank([nm.join(" "), lt.join(" ")]), i: i }); });
    [P, S].forEach(function (a) { var c = [0, 0, 0]; a.sort(function (x, y) { return x.k - y.k || x.i - y.i; }); a.forEach(function (x) { x.pos = c[x.k]++; }); });
    return P.concat(S).sort(function (a, b) { return a.k - b.k || a.pos - b.pos || (a.t === b.t ? 0 : a.t === "p" ? -1 : 1); }).slice(0, sugMax());
  }
  function sugImg(box, p, fallback) {
    box.innerHTML = '<img src="' + esc(p.src) + '" alt="" referrerpolicy="no-referrer" loading="lazy"' + photoAttrs(p, "remove") + '>';
    var im = box.querySelector("img"); im.onerror = function () { if (!photoFallback(im, "remove")) box.innerHTML = fallback; };
  }
  function sugDraw() {
    if (!SUG.rows.length) { sugBox.hidden = true; sugBox.innerHTML = ""; sugIn.setAttribute("aria-expanded", "false"); return; }
    sugBox.innerHTML = "";
    SUG.rows.forEach(function (r) {
      var row = document.createElement("div"), e = r.t === "p" ? ECO_BY[r.id] : null, ico = e ? '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">' + (ICONS[e.icon] || "") + "</svg>" : SUG_LEAF;
      row.className = "sgr"; row.setAttribute("role", "option"); if (r.t === "p") row.setAttribute("data-id", r.id); else row.setAttribute("data-latin", r.latin);
      row.innerHTML = '<span class="sgi">' + ico + '</span><span class="sgt"><b></b><i></i></span>' + SUG_CHEV;
      row.querySelector("b").textContent = r.name;
      row.querySelector("i").textContent = r.t === "p" ? (e && e.place ? "Place · " + e.place : "Place") : "Species · in " + r.n + (r.n === 1 ? " place" : " places");
      var p = r.t === "p" ? (e && e.imgwiki && PHOTOS[e.imgwiki]) : PHOTOS[r.latin];
      if (p) sugImg(row.querySelector(".sgi"), p, ico);
      sugBox.appendChild(row);
    });
    sugBox.hidden = false; sugIn.setAttribute("aria-expanded", "true");
  }
  function sugFile(k) {   /* the suggestion file of one two-letter start; empty when the build has none */
    if (!SRCH.meta) SRCH.meta = srchGet("meta.json");
    return SRCH.meta.then(function (m) { return !m.sug || m.sug.indexOf(k) < 0 ? { p: [], s: [] } : SUG.bk[k] || (SUG.bk[k] = srchGet("s-" + k + ".json")); });
  }
  /* The result header (#425): when the text is exactly one species or place, a line above the list says so, with a link to its page; after "Show on the map" it is the visible filter,
     "Places with Osprey" and a way to clear it. For a species each card of its places also says "Has osprey" (the places come from the species-places file, as for the filter). */
  var QH = { k: "", n: 0 };
  function qHead() {
    var hd = document.getElementById("qhead"); if (!hd) return;
    var q = FL.q || "", key = q + "|" + !!FL.busy + "|" + (M.chip === q); if (QH.k === key) return;
    QH.k = key; var n = ++QH.n, ws = srchWords(q), last = ws[ws.length - 1];
    hd.hidden = true; M.why = null; whyLines();
    if (!last || last.length < 2 || FL.busy) return;
    sugFile(last.slice(0, 2)).then(function (d) {
      var r = sugPick(q, d)[0]; if (n !== QH.n || !r || r.k) return;
      var sp = r.t === "s", e = ECO_BY[r.id], nm = escH(r.name), chip = sp && M.chip === q;
      hd.className = "qhead" + (chip ? " qchip" : "");
      hd.innerHTML = chip ? "Places with <b>" + nm + '</b> <a href="#" data-hx="1" aria-label="Clear the filter">\u2715</a>'
        : "<b>" + nm + "</b> \u00b7 " + (sp ? "found in " + r.n + (r.n === 1 ? " place" : " places") + ' \u00b7 <a href="#" data-hsp="' + esc(r.latin) + '">Species page \u203a</a>' : '<a href="#" data-hpl="' + r.id + '">Open the place \u203a</a>');
      hd.hidden = false;
      if (sp) sppPlaces(r.latin).then(function (ids) { if (n === QH.n) { M.why = { s: new Set(ids), t: "Has " + r.name.toLowerCase() }; whyLines(); } });
    }).catch(function () {});
  }
  function whyLines() {   /* the muted line on a card that says why it is in the result */
    ECOS.forEach(function (e) {
      if (!e.li) return;
      var w = e.li.querySelector(".why"), t = M.why && M.why.s.has(e.id) ? M.why.t : "";
      if (!t) { if (w) w.remove(); return; }
      if (!w) { w = document.createElement("span"); w.className = "why"; e.li.querySelector(".card").appendChild(w); }
      w.textContent = t;
    });
  }
  document.getElementById("qhead").addEventListener("click", function (ev) {
    var a = ev.target.closest("a"); if (!a) return; ev.preventDefault();
    if (a.hasAttribute("data-hsp")) showSpecies(sidOf({ latin: a.getAttribute("data-hsp") }));
    else if (a.hasAttribute("data-hpl")) showPlace(a.getAttribute("data-hpl"));
    else document.getElementById("qclr").click();
  });
  function sugShow() {
    var raw = sugIn.value.trim(), ws = srchWords(raw), last = ws[ws.length - 1];
    if (!last || last.length < 2 || document.activeElement !== sugIn) { sugHide(); return; }
    var n = ++SUG.n; SUG.q = raw;
    sugFile(last.slice(0, 2)).then(function (d) {
      if (n !== SUG.n) return;   /* the text has moved on */
      SUG.rows = sugPick(raw, d); sugDraw();
      if (!Places.done) Places.loadLocals().then(function () { if (n === SUG.n) sugDraw(); });   /* the place lines and icons of local places */
      withSpeciesPhotos(function () { if (n === SUG.n) sugDraw(); });
    }).catch(function () { if (n === SUG.n) sugHide(); });   /* no suggestions when the file cannot be had; the normal search goes on */
  }
  if (sugBox) {
    sugIn.addEventListener("input", sugShow);
    sugIn.addEventListener("focus", sugShow);
    sugIn.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === "Escape") sugHide(); });
    sugBox.addEventListener("pointerdown", function (ev) { ev.preventDefault(); });   /* keep the focus in the box until the row is chosen */
    sugBox.addEventListener("click", function (ev) {
      var row = ev.target.closest(".sgr"); if (!row) return;
      var id = row.getAttribute("data-id"), latin = row.getAttribute("data-latin"), name = row.querySelector("b").textContent;
      sugHide(); sugIn.blur();
      if (id) showPlace(id);
      else speciesMap(name, latin);
    });
    document.addEventListener("pointerdown", function (ev) { if (!ev.target.closest("#qwrap")) sugHide(); }, true);
  }
