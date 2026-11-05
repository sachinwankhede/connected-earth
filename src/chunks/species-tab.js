/* The Species tab (#422). This code is not in the page: the page loads this file the first time the tab opens (withSpeciesTab in src/app/cards.js) and gives it what it
   needs in A (Data, the photo registry, escaping, the row icons, and go(latin) which opens a species page). It reads api/species-tab/ only through A.Data.
   First screen: the species found in the most places, then the groups; a group opens its own list, 250 rows at a time. */
window.__chunk = window.__chunk || {};
window.__chunk["species-tab"] = function (A) {
  var box = document.getElementById("sptab"), started = false, top = [], groups = [];
  function el(html, cls) { var d = document.createElement("div"); d.className = cls; d.innerHTML = html; return d; }
  function row(r) {   /* [Latin name, usual name, places, picture file or 0] */
    var c = r[3] && A.PhotoRegistry.speciesCandidate([r[3], r[0]], r[0], 1, null);
    var d = el('<span class="sgi">' + (c ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + A.esc(c.assetUrl) + '">' : A.leaf) + '</span><span class="sgt"><b></b><i></i></span>' + A.chev, "sgr");
    d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-latin", r[0]);
    d.querySelector("b").textContent = r[1]; d.querySelector("i").textContent = "Species · in " + r[2] + (r[2] === 1 ? " place" : " places");
    var im = d.querySelector("img"); if (im) im.onerror = function () { d.querySelector(".sgi").innerHTML = A.leaf; };
    return d;
  }
  function groupRow(g) {   /* [key, label, species, pages] */
    var d = el('<span class="sgi">' + A.leaf + '</span><span class="sgt"><b></b><i></i></span>' + A.chev, "sgr");
    d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-g", g[0]);
    d.querySelector("b").textContent = g[1]; d.querySelector("i").textContent = g[2] + (g[2] === 1 ? " species" : " species");
    return d;
  }
  function list(items, make) { var l = el("", "sgl"); items.forEach(function (x) { l.appendChild(make(x)); }); return l; }
  function home() {
    box.innerHTML = "<h3>Found in the most places</h3>"; box.appendChild(list(top, row));
    box.insertAdjacentHTML("beforeend", "<h3>Browse by group</h3>"); box.appendChild(list(groups, groupRow));
  }
  function group(g) {   /* one group: its first page, and "Show more" for the next */
    var page = 0, shown = 0;
    box.innerHTML = '<button type="button" class="jback" data-up="1">‹ Species</button><h3></h3>';
    box.querySelector("h3").textContent = g[1] + " · " + g[2];
    var l = el("", "sgl"), p = el('<a href="#" data-more="1"></a>', "fine"); box.appendChild(l); box.appendChild(p); p.hidden = true;
    function more() {
      var k = page++;
      A.Data.speciesTab("g-" + g[0] + "-" + k + ".json").then(function (rows) {
        rows.forEach(function (r) { l.appendChild(row(r)); }); shown += rows.length;
        p.hidden = shown >= g[2]; p.firstChild.textContent = "Show " + Math.min(g[2] - shown, 250) + " more ›";
      }).catch(function () { page = k; p.hidden = false; p.firstChild.textContent = "Could not load. Try again"; });
    }
    p.addEventListener("click", function (ev) { ev.preventDefault(); more(); });
    more();
  }
  function act(t) {
    var d = t.closest(".sgr"), g;
    if (d && d.hasAttribute("data-latin")) A.go(d.getAttribute("data-latin"));
    else if (d && (g = groups.filter(function (x) { return x[0] === d.getAttribute("data-g"); })[0])) group(g);
    else if (t.closest("[data-up]")) { home(); box.scrollIntoView && box.scrollIntoView({ block: "start" }); }
  }
  box.addEventListener("click", function (ev) { act(ev.target); });
  box.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); act(ev.target); } });
  return {
    open: function () {
      if (started) return; started = true;
      Promise.all([A.Data.speciesTab("top.json"), A.Data.speciesTab("groups.json")]).then(function (r) { top = r[0]; groups = r[1]; home(); })
        .catch(function () { started = false; box.innerHTML = '<p class="fine">The species could not be loaded. Check your connection and try again.</p>'; });
    }
  };
};
