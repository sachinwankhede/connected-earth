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
  var RS_CLOCK = SUG_LEAF.replace(/<path.*<\/svg>/, '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>');
  /* Recent searches (#589): the last three things the person opened or searched, kept in this browser only (localStorage "ceRs"), shown as dropdown rows while the box is empty and focused */
  function rsGet() { try { return JSON.parse(localStorage.getItem("ceRs")) || []; } catch (e) { return []; } }
  function rsAdd(o) { try { var k = function (x) { return x.t + (x.id || x.latin || x.q); }, a = rsGet().filter(function (x) { return k(x) !== k(o); }); localStorage.setItem("ceRs", JSON.stringify([o].concat(a).slice(0, 3))); } catch (e) {} }
  function sugMax() { return window.matchMedia && matchMedia("(max-width: 700px)").matches ? 3 : 5; }
  function sugHide() { SUG.n++; SUG.rows = []; if (sugBox) { sugBox.hidden = true; sugBox.innerHTML = ""; } sugIn.setAttribute("aria-expanded", "false"); }
  /* rows for the typed text q out of one suggestion file d: every typed word must start a word of the name. Rank k: 0 the whole name (or Latin name) is what was typed, 1 the
     name starts with it, 2 only a word of the name starts with it. Within a rank the better known first: a place by its position in the home list, a species by its number of
     places; the two kinds are interleaved by that position (the best place, the best species, the second place, ...), so the type alone never decides (#424) */
  function sugPick(q, d, max) {
    var ws = srchWords(q), phrase = ws.join(" "), P = [], S = [];
    if (!ws.length) return [];
    function words(label) { return srchWords(label); }
    function has(lw) { return ws.every(function (w) { return lw.some(function (x) { return x.lastIndexOf(w, 0) === 0; }); }); }
    function rank(names) { var r = 2; names.forEach(function (n) { r = Math.min(r, n === phrase ? 0 : n.lastIndexOf(phrase, 0) === 0 ? 1 : 2); }); return r; }
    (d.p || []).forEach(function (r, i) { var nm = words(r[1]); if (has(nm)) P.push({ t: "p", id: r[0], name: r[1], k: rank([nm.join(" ")]), i: i }); });
    (d.s || []).forEach(function (r, i) { var nm = words(r[1]), lt = words(r[0]); if (has(nm.concat(lt, words(r[4] || "")))) S.push({ t: "s", latin: r[0], name: r[1], n: r[2], pic: r[3], k: rank([nm.join(" "), lt.join(" ")]), i: i }); });
    [P, S].forEach(function (a) { var c = [0, 0, 0]; a.sort(function (x, y) { return x.k - y.k || x.i - y.i; }); a.forEach(function (x) { x.pos = c[x.k]++; }); });
    return P.concat(S).sort(function (a, b) { return a.k - b.k || a.pos - b.pos || (a.t === b.t ? 0 : a.t === "p" ? -1 : 1); }).slice(0, max || sugMax());
  }
  function sugImg(box, p, fallback) {
    box.innerHTML = '<img src="' + esc(p.src) + '" alt="" referrerpolicy="no-referrer" loading="lazy"' + photoAttrs(p, "remove") + '>';
    var im = box.querySelector("img"); im.onerror = function () { if (!photoFallback(im, "remove")) box.innerHTML = fallback; };
  }
  function sugDraw() {
    if (!SUG.rows.length) { sugBox.hidden = true; sugBox.innerHTML = ""; sugIn.setAttribute("aria-expanded", "false"); return; }
    sugBox.innerHTML = "";
    if (SUG.rows[0].rc) { var h = document.createElement("div"); h.className = "sgh"; h.textContent = "Recent"; sugBox.appendChild(h); }   /* one label for the recent searches, not a prefix on every row */
    SUG.rows.forEach(function (r) {
      var c, row = document.createElement("div"), e = r.t === "p" ? ECO_BY[r.id] : null, ico = r.t === "q" ? RS_CLOCK : e ? '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">' + (ICONS[e.icon] || "") + "</svg>" : SUG_LEAF;
      row.className = r.t === "q" ? "sgr sgq" : "sgr"; row.setAttribute("role", "option"); if (r.t === "p") row.setAttribute("data-id", r.id); else if (r.t === "s") row.setAttribute("data-latin", r.latin); else row.setAttribute("data-q", r.q);
      row.innerHTML = '<span class="sgi">' + ico + '</span><span class="sgt"><b></b>' + (r.t === "q" ? "" : "<i></i>") + "</span>" + (r.t === "q" ? "" : SUG_CHEV);   /* a typed search: one line, no chevron (a chevron opens a page) */
      row.querySelector("b").textContent = r.name || r.q;
      if (r.t !== "q") row.querySelector("i").textContent = r.t === "p" ? (e && e.place ? "Place · " + e.place : "Place") : "Species · in " + r.n + (r.n === 1 ? " place" : " places");;
      var p = r.t === "q" ? 0 : r.t === "p" ? (e && e.imgwiki && PHOTOS[e.imgwiki]) : PHOTOS[r.latin] || (r.pic && (c = PhotoRegistry.speciesCandidate([r.pic, r.latin], r.latin, 1, null)) && { src: c.assetUrl, key: r.latin });   /* the hosted picture is in the row itself (#443) */
      if (p) sugImg(row.querySelector(".sgi"), p, ico);
      sugBox.appendChild(row);
    });
    var need = SUG.rows.map(function (r) { var e = r.t === "p" && ECO_BY[r.id]; return e && e.imgwiki && !PHOTOS[e.imgwiki] ? e.imgwiki : ""; }).filter(Boolean), k = need.join("|");
    if (k && k !== SUG.pk) { SUG.pk = k; M.placePhotos(need, function () { if (!sugBox.hidden) sugDraw(); }); }   /* a place row without its picture asks for it once, then draws again (a place with no picture is not asked twice) */
    sugBox.hidden = false; sugIn.setAttribute("aria-expanded", "true");
  }
  function sugFile(k) {   /* the suggestion file of one two-letter start; empty when the build has none */
    if (!SRCH.meta) SRCH.meta = srchGet("meta.json");
    return SRCH.meta.then(function (m) { return !m.sug || m.sug.indexOf(k) < 0 ? { p: [], s: [] } : SUG.bk[k] || (SUG.bk[k] = srchGet("s-" + k + ".json")); });
  }
  /* The result header (#425): when the text is exactly one species or place, a line above the list says so, with a link to its page; after "Show on the map" it is the visible filter,
     "Places with Osprey" and a way to clear it. The places of a species are one tap away on the header ("found in N places"); the Places list itself matches by name (#480). */
  var QH = { k: "", n: 0 };
  function qHead() {
    var hd = document.getElementById("qhead"); if (!hd) return;
    var q = FL.q || "", key = q + "|" + !!FL.busy + "|" + (M.chip === q) + "|" + M.tab; if (QH.k === key) return;
    QH.k = key; var n = ++QH.n, ws = srchWords(q), last = ws[ws.length - 1];
    hd.hidden = true; tabCount("species", null); document.getElementById("sheet").classList.toggle("mm", M.chip === q && !!q);
    if (!last || last.length < 2 || FL.busy) return;
    sugFile(last.slice(0, 2)).then(function (d) {
      if (n !== QH.n) return; var sn = sugPick(q, { s: d.s }, 40).length; tabCount("species", sn < 40 ? sn : "40+");
      var r = sugPick(q, d)[0]; if (!r || r.k) return;
      var sp = r.t === "s", e = ECO_BY[r.id], nm = escH(r.name), chip = sp && M.chip === q;
      hd.className = "qhead" + (chip ? " qchip" : "");
      if (chip) { withSpeciesTab(function (c) { c.mapHead(hd, r); hd.hidden = false; }); return; }
      hd.innerHTML = "<b>" + nm + "</b> \u00b7 " + (sp ? 'found in <a href="#" data-hmap="' + esc(r.latin) + '" data-hn="' + esc(r.name) + '">' + r.n + (r.n === 1 ? " place" : " places") + '</a> \u00b7 <a href="#" data-hsp="' + esc(r.latin) + '">Species page \u203a</a>' : '<a href="#" data-hpl="' + r.id + '">Open the place \u203a</a>');
      hd.hidden = M.tab === "journeys";   /* the Journeys tab says what it found once, in the note */
    }).catch(function () {});
  }
  document.getElementById("qhead").addEventListener("click", function (ev) {
    var a = ev.target.closest("a"); if (!a) return; ev.preventDefault();
    if (a.hasAttribute("data-hsp")) showSpecies(sidOf({ latin: a.getAttribute("data-hsp") }));
    else if (a.hasAttribute("data-hmap")) speciesMap(a.getAttribute("data-hn"), a.getAttribute("data-hmap"));   /* the places of the species, on the map (the search list is by name) */
    else if (a.hasAttribute("data-hpl")) showPlace(a.getAttribute("data-hpl"));
    else withSpeciesTab(function (c) { c.mapBack(); });
  });
  function sugShow() {
    var raw = sugIn.value.trim(), ws = srchWords(raw), last = ws[ws.length - 1];
    if (!raw && document.activeElement === sugIn) {   /* the empty box: the recent searches (species only on the Species tab) */
      var sp = document.getElementById("sbody").classList.contains("tab-s"), n0 = ++SUG.n;
      SUG.rows = rsGet().filter(function (x) { return !sp || x.t === "s"; }).map(function (x) { x.rc = 1; return x; }); sugDraw();
      if (SUG.rows.some(function (x) { return x.t === "p"; }) && !Places.done) Places.loadLocals().then(function () { if (n0 === SUG.n) sugDraw(); });
      withSpeciesPhotos(function () { if (n0 === SUG.n) sugDraw(); }); return;
    }
    if (!last || last.length < 2 || document.activeElement !== sugIn) { sugHide(); return; }
    var n = ++SUG.n; SUG.q = raw;
    sugFile(last.slice(0, 2)).then(function (d) {
      if (n !== SUG.n) return;   /* the text has moved on */
      SUG.rows = sugPick(raw, document.getElementById("sbody").classList.contains("tab-s") ? { s: d.s } : d); sugDraw();   /* on the Species tab only species (#422) */
      if (!Places.done) Places.loadLocals().then(function () { if (n === SUG.n) sugDraw(); });   /* the place lines and icons of local places */
      withSpeciesPhotos(function () { if (n === SUG.n) sugDraw(); });
    }).catch(function () { if (n === SUG.n) sugHide(); });   /* no suggestions when the file cannot be had; the normal search goes on */
  }
  function sheetUp() { if (M.setSheet && M.sheetState === "min") M.setSheet("half"); }
  if (sugBox) {
    sugIn.addEventListener("input", sugShow);
    sugIn.addEventListener("focus", sugShow);
    sugIn.addEventListener("keydown", function (ev) { if (ev.key === "Enter" && sugIn.value.trim().length > 1) rsAdd({ t: "q", q: sugIn.value.trim() }), sheetUp(); if (ev.key === "Enter" || ev.key === "Escape") sugHide(); });
    sugIn.addEventListener("search", function () { sugHide(); sugIn.blur(); });
    sugBox.addEventListener("pointerdown", function (ev) { ev.preventDefault(); });   /* keep the focus in the box until the row is chosen */
    sugBox.addEventListener("click", function (ev) {
      var row = ev.target.closest(".sgr"); if (!row) return;
      var id = row.getAttribute("data-id"), latin = row.getAttribute("data-latin"), name = row.querySelector("b").textContent, q = row.getAttribute("data-q"), rw = SUG.rows[[].indexOf.call(sugBox.querySelectorAll(".sgr"), row)];   /* the "Recent" label is a child too: count rows only */
      sugHide(); sugIn.blur();
      if (rw) rw.rc = 0, rsAdd(rw);
      if (q) runSearch(q), sheetUp();
      else if (id) showPlace(id);
      else { if (FL.q !== sugIn.value.trim().toLowerCase()) runSearch(sugIn.value); showSpecies(sidOf({ latin: latin })); }   /* the typed search is what Back returns to, even when the throttled search has not run yet */   /* a species row opens its page (#420 step 3); "Show on the map" is there */
    });
    document.addEventListener("pointerdown", function (ev) { if (!ev.target.closest("#qwrap")) sugHide(); }, true);
  }
