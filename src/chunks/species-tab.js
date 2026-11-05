/* The Species tab (#422). This code is not in the page: the page loads this file the first time the tab opens (withSpeciesTab in src/app/cards.js) and gives it what it
   needs in A (Data, the photo registry, escaping, the row icons, and go(latin) which opens a species page). It reads api/species-tab/ only through A.Data. */
window.__chunk = window.__chunk || {};
window.__chunk["species-tab"] = function (A) {
  var box = document.getElementById("sptab"), started = false;
  function row(r) {   /* [Latin name, usual name, places, picture file or 0] */
    var d = document.createElement("div"), c = r[3] && A.PhotoRegistry.speciesCandidate([r[3], r[0]], r[0], 1, null);
    d.className = "sgr"; d.setAttribute("role", "link"); d.tabIndex = 0; d.setAttribute("data-latin", r[0]);
    d.innerHTML = '<span class="sgi">' + (c ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + A.esc(c.assetUrl) + '">' : A.leaf) + '</span><span class="sgt"><b></b><i></i></span>' + A.chev;
    d.querySelector("b").textContent = r[1]; d.querySelector("i").textContent = "Species · in " + r[2] + (r[2] === 1 ? " place" : " places");
    var im = d.querySelector("img"); if (im) im.onerror = function () { d.querySelector(".sgi").innerHTML = A.leaf; };
    return d;
  }
  box.addEventListener("click", function (ev) { var d = ev.target.closest(".sgr"); if (d) A.go(d.getAttribute("data-latin")); });
  box.addEventListener("keydown", function (ev) { var d = ev.target.closest(".sgr"); if (d && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); A.go(d.getAttribute("data-latin")); } });
  return {
    open: function () {
      if (started) return; started = true;
      box.innerHTML = "<h3>Found in the most places</h3>"; var list = document.createElement("div"); list.className = "sgl"; box.appendChild(list);
      A.Data.speciesTab("top.json").then(function (rows) { rows.forEach(function (r) { list.appendChild(row(r)); }); })
        .catch(function () { started = false; box.innerHTML = '<p class="fine">The species could not be loaded. Check your connection and try again.</p>'; });
    }
  };
};
