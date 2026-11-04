  /* Suggestions while typing (#413): a short dropdown under the search box. The rows come from api/search[-pilot]/s-<first two letters of the last typed word>.json
     (written by the build): places in home-list order and species with the number of places. A name that starts with what is typed comes before a name that only has
     a word that starts with it; places before species within each. At most 3 rows on a phone, 5 on a wider screen. A place row opens the place, a species row runs
     "Show on the map" for that species. The dropdown shows only while the box has focus and at least two letters are typed; Enter, Clear, a tap on a row or a tap
     elsewhere closes it. Nothing here blocks the normal search, which still runs on every keystroke. */
  var SUG = { bk: {}, n: 0, rows: [], q: "" };
  var sugBox = document.getElementById("sug"), sugIn = document.getElementById("q");
  var SUG_LEAF = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19c3-4 6-7 9-9"/></svg>';
  var SUG_CHEV = '<svg class="sgo" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
  function sugMax() { return window.matchMedia && matchMedia("(max-width: 700px)").matches ? 3 : 5; }
  function sugHide() { SUG.n++; SUG.rows = []; if (sugBox) { sugBox.hidden = true; sugBox.innerHTML = ""; } sugIn.setAttribute("aria-expanded", "false"); }
  /* rows for the typed text q out of one suggestion file d: every typed word must start a word of the name, then starts-with, then places before species */
  function sugPick(q, d) {
    var ws = srchWords(q), phrase = ws.join(" "), list = [];
    if (!ws.length) return list;
    function words(label) { return srchWords(label); }
    function has(lw) { return ws.every(function (w) { return lw.some(function (x) { return x.lastIndexOf(w, 0) === 0; }); }); }
    (d.p || []).forEach(function (r, i) { var nm = words(r[1]); if (has(nm)) list.push({ t: "p", id: r[0], name: r[1], k: (nm.join(" ").lastIndexOf(phrase, 0) === 0 ? 0 : 1) * 2, i: i }); });
    (d.s || []).forEach(function (r, i) { var nm = words(r[1]), lt = words(r[0]); if (has(nm.concat(lt))) list.push({ t: "s", latin: r[0], name: r[1], n: r[2], k: (nm.join(" ").lastIndexOf(phrase, 0) === 0 || lt.join(" ").lastIndexOf(phrase, 0) === 0 ? 0 : 1) * 2 + 1, i: i }); });
    list.sort(function (a, b) { return (a.k >> 1) - (b.k >> 1) || (a.t === b.t ? a.i - b.i : a.t === "p" ? -1 : 1); });
    return list.slice(0, sugMax());
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
      row.querySelector("i").textContent = r.t === "p" ? (e ? e.place : "Place") : "Species · in " + r.n + (r.n === 1 ? " place" : " places");
      var p = r.t === "p" ? (e && e.imgwiki && PHOTOS[e.imgwiki]) : PHOTOS[r.latin];
      if (p) sugImg(row.querySelector(".sgi"), p, ico);
      sugBox.appendChild(row);
    });
    sugBox.hidden = false; sugIn.setAttribute("aria-expanded", "true");
  }
  function sugShow() {
    var raw = sugIn.value.trim(), ws = srchWords(raw), last = ws[ws.length - 1];
    if (!last || last.length < 2 || document.activeElement !== sugIn) { sugHide(); return; }
    var n = ++SUG.n; SUG.q = raw;
    if (!SRCH.meta) SRCH.meta = srchGet("meta.json");
    SRCH.meta.then(function (m) {
      var k = last.slice(0, 2);
      if (!m.sug || m.sug.indexOf(k) < 0) return { p: [], s: [] };
      return SUG.bk[k] || (SUG.bk[k] = srchGet("s-" + k + ".json"));
    }).then(function (d) {
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
