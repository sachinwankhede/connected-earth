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

  function speciesAsset(value) {
    if (typeof value !== "string" || !value) return null;
    if (/^https:\/\//i.test(value)) return httpsUrl(value, ALLOWED_HOSTS) ? value : null;
    var decoded = value;
    try { decoded = decodeURIComponent(value); } catch (e) { return null; }
    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.charAt(0) === "/" || decoded.split("/").some(function (part) { return part === "." || part === ".."; }) || /[?#]/.test(value)) return null;
    return "https://thumb.wikimedia.org/wikipedia/commons/thumb/" +
      value.replace(/\/(page1-)?330px-/, function (_, page) { return "/" + (page || "") + "120px-"; });
  }

  function speciesCandidate(value, sourcePage, priority, metadata) {
    if (!Array.isArray(value) || value.length < 2) return null;
    var assetUrl = speciesAsset(value[0]);
    var page = wikiUrl(value[1]);
    var credit = metadata && typeof metadata === "object" ? metadata : null;
    if (!assetUrl) return null;
    return {
      provider: "wikimedia-commons",
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
    nextCandidate: nextCandidate,
    placeCandidate: placeCandidate,
    register: register,
    speciesCandidate: speciesCandidate,
    validateCandidate: validateCandidate,
    wikiUrl: wikiUrl
  };
});
