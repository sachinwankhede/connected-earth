(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PhotoRegistry = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  var ALLOWED_HOSTS = { "upload.wikimedia.org": true, "thumb.wikimedia.org": true };
  var IMAGE_TYPES = { "image/jpeg": true, "image/png": true, "image/gif": true, "image/webp": true };

  function httpsUrl(value, hosts) {
    if (typeof value !== "string" || !value) return false;
    try {
      var u = new URL(value);
      return u.protocol === "https:" && (!hosts || hosts[u.hostname] === true) && !u.username && !u.password;
    } catch (e) {
      return false;
    }
  }

  function wikiUrl(title) {
    var decoded = String(title || "");
    try { decoded = decodeURIComponent(decoded); } catch (e) {}
    return "https://en.wikipedia.org/wiki/" + encodeURIComponent(decoded.replace(/ /g, "_"));
  }

  // Species pictures are our own hosted copies: an entry holds the hosted file name (12 hex digits and .webp), and the file is read from
  // <species base>/<name>. Nothing else is accepted, so a picture is never fetched from another site.
  var speciesBase = "photos/species/";
  function setSpeciesBase(base) { speciesBase = String(base || "photos/species/"); }
  function speciesAsset(value) {
    if (typeof value !== "string" || !/^[0-9a-f]{12}\.webp$/.test(value)) return null;
    return speciesBase + value;
  }

  function speciesCandidate(value, sourcePage, priority, metadata) {
    if (!Array.isArray(value) || value.length < 2) return null;
    var assetUrl = speciesAsset(value[0]);
    var page = wikiUrl(value[1]);
    var credit = metadata && typeof metadata === "object" ? metadata : null;
    if (!assetUrl) return null;
    return {
      provider: "hosted",
      assetUrl: assetUrl,
      sourcePageUrl: page,
      author: credit && credit.a || null,
      licenseId: credit && credit.l || null,
      licenseUrl: credit && credit.lu || null,
      reviewStatus: "legacy",
      legacyCredit: credit && credit.a && credit.l && credit.p ? {
        a: credit.a,
        l: credit.l,
        lu: credit.lu || "",
        p: credit.p
      } : null,
      checkedAt: value.checkedAt || null,
      fetchedAt: value.fetchedAt || null,
      mediaType: null,
      width: null,
      height: null,
      mirrorPath: null,
      mirrorHash: null,
      priority: priority || 1
    };
  }

  // A journey cover is its own picture row keyed by journey id: {id: [cover file, page]} (192 px since #1188; an older cover is 96 px under the same name) (jpic) with its credit (jpicm) in api/species-pictures.json. The file is read from <base>/<name>.
  function journeyCandidate(value, base, metadata) {
    if (!Array.isArray(value) || typeof value[0] !== "string" || !/^[\w-]+\.webp$/.test(value[0]) || typeof base !== "string") return null;
    var c = speciesCandidate(["000000000000.webp", value[1]], null, 1, metadata);
    c.assetUrl = base + value[0];
    c.sourcePageUrl = value[1] ? (/^https?:/.test(value[1]) ? value[1] : wikiUrl(value[1])) : null;
    return c;
  }
  function coverKey(id) { return "journey:" + id; }
  // A non-species node (sunlight, rain, soil, decomposers...) has its picture by node id (`nid`, written into the node by the build, #1007). The file is one of our own copies, read from <base>/<name>.
  function nodeKey(id) { return "node:" + id; }
  function nodeCandidate(value, base, metadata) {
    if (!Array.isArray(value) || typeof value[0] !== "string" || !/^[0-9a-f]{12}\.webp$/.test(value[0]) || typeof base !== "string") return null;
    var c = speciesCandidate(["000000000000.webp", value[1]], null, 1, metadata);
    c.assetUrl = base + value[0];
    c.sourcePageUrl = value[1] ? (/^https?:/.test(value[1]) ? value[1] : wikiUrl(value[1])) : null;
    return c;
  }
  // A place's picture is registered under its place id (never its Wikipedia title, which two places can share, #908, #968).
  function placeKey(id) { return "place:" + id; }
  // A species' picture is registered under its species id (`sid`, written by the build as the slug of its Latin name), never its Latin name or a Wikipedia title that two species can share (#934, #974).
  function speciesKey(sid) { return "species:" + sid; }
  // The picture a journey shows as its cover: its own row by journey id (#973 phase 4: no title fallback; a journey without a row shows its icon).
  function coverPhoto(photos, c) { return c && photos[coverKey(c.id)] || null; }
  // The credit rows of a journey page: the cover, then the two end places' pictures (by title), one per picture (same src; the end places by their place key).
  function coverCredits(photos, c, endKeys) {
    var seen = {}, out = [];
    [coverPhoto(photos, c)].concat((endKeys || []).map(function (w) { return w && photos[w]; })).forEach(function (p) {
      if (!p || seen[p.src]) return;
      seen[p.src] = 1; out.push(p);
    });
    return out;
  }

  function placeCandidate(value, assetBase) {
    if (!value || typeof value !== "object" || typeof value.f !== "string") return null;
    var file = value.f;
    if (!file || file.charAt(0) === "/" || file.indexOf("..") >= 0 || /[?#]/.test(file)) return null;
    return {
      provider: "wikimedia-commons",
      assetUrl: assetBase + file,
      sourcePageUrl: value.p || value.w || null,
      author: value.a || null,
      licenseId: value.l || null,
      licenseUrl: value.lu || null,
      reviewStatus: value.reviewStatus || (value.a && value.a.toLowerCase() !== "unknown author" &&
        value.l && value.l.toLowerCase().indexOf("see ") !== 0 && value.mt && value.width > 0 && value.height > 0 &&
        ((value.lu && httpsUrl(value.lu)) || /^(public domain|cc0)$/i.test(value.l)) && httpsUrl(value.p) ? "approved" : "legacy"),
      checkedAt: null,
      fetchedAt: null,
      mediaType: value.mt || null,
      width: value.width || null,
      height: value.height || null,
      mirrorPath: file,
      mirrorHash: value.sha256 || null,
      priority: 0,
      legacyCredit: value
    };
  }

  function validateCandidate(candidate, options) {
    options = options || {};
    var errors = [];
    if (!candidate || typeof candidate !== "object") return ["candidate must be an object"];
    if (!candidate.provider) errors.push("provider is required");
    var asset = candidate.assetUrl || "";
    var local = options.allowLocal && typeof asset === "string" && /^(?:photos\/|\/photos\/)/.test(asset);
    if (!local && !httpsUrl(asset, options.allowedHosts || ALLOWED_HOSTS)) errors.push("asset URL must use HTTPS and an approved provider host");
    if (!httpsUrl(candidate.sourcePageUrl)) errors.push("source page URL must use HTTPS");
    if (!candidate.author) errors.push("author is required");
    if (!candidate.licenseId) errors.push("license identifier is required");
    if (candidate.licenseUrl && !httpsUrl(candidate.licenseUrl)) errors.push("license URL must use HTTPS");
    if (candidate.licenseId && !/public domain/i.test(candidate.licenseId) && !candidate.licenseUrl) errors.push("license URL is required");
    if (!IMAGE_TYPES[candidate.mediaType]) errors.push("media type must be a supported image MIME type");
    if (!Number.isInteger(candidate.width) || candidate.width <= 0 || !Number.isInteger(candidate.height) || candidate.height <= 0) errors.push("positive image dimensions are required");
    if (candidate.reviewStatus !== "approved") errors.push("candidate is not approved");
    return errors;
  }

  function register(registry, key, candidate) {
    if (!key || !candidate || (candidate.reviewStatus !== "approved" && candidate.reviewStatus !== "legacy")) return;
    var entry = registry[key];
    if (!entry) entry = registry[key] = { key: key, candidates: [] };
    if (entry.candidates.some(function (c) { return c.assetUrl === candidate.assetUrl; })) return;
    entry.candidates.push(candidate);
    entry.candidates.sort(function (a, b) { return (a.priority || 0) - (b.priority || 0); });
    var first = entry.candidates[0];
    entry.src = first.assetUrl;
    entry.page = first.sourcePageUrl;
    entry.credit = first.legacyCredit || (first.author && first.licenseId ? {
      a: first.author,
      l: first.licenseId,
      lu: first.licenseUrl,
      p: first.sourcePageUrl
    } : null);
  }

  function nextCandidate(candidates, currentIndex, attempted) {
    attempted = attempted || {};
    for (var i = (currentIndex || 0) + 1; i < (candidates || []).length; i++) {
      var candidate = candidates[i];
      if ((candidate.reviewStatus !== "approved" && candidate.reviewStatus !== "legacy") || attempted[candidate.assetUrl]) continue;
      return { index: i, url: candidate.assetUrl };
    }
    return null;
  }

  return {
    coverCredits: coverCredits,
    coverKey: coverKey,
    nodeKey: nodeKey,
    nodeCandidate: nodeCandidate,
    coverPhoto: coverPhoto,
    journeyCandidate: journeyCandidate,
    placeKey: placeKey,
    speciesKey: speciesKey,
    nextCandidate: nextCandidate,
    placeCandidate: placeCandidate,
    register: register,
    speciesCandidate: speciesCandidate,
    setSpeciesBase: setSpeciesBase,
    validateCandidate: validateCandidate,
    wikiUrl: wikiUrl
  };
});
