  var LAND = __LAND__;
  var GEO = __GEO__;

  var TL = {
    0: { label: "Environment & decomposers", short: "Environment" },
    1: { label: "Producers", short: "Producer" },
    2: { label: "Herbivores & grazers", short: "Primary consumer" },
    3: { label: "Mesopredators & scavengers", short: "Secondary consumer" },
    4: { label: "Apex predators", short: "Apex predator" }
  };

  /* ---------- Glyphs: hand-drawn 24x24 icons shown when a photo is not available ---------- */
  var S = ' fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"';
  var QUAD = '<ellipse cx="11" cy="12" rx="6.5" ry="3.8"/><rect x="5.5" y="14" width="1.8" height="6.5" rx=".9"/><rect x="8.2" y="14.5" width="1.8" height="6" rx=".9"/><rect x="12.4" y="14.5" width="1.8" height="6" rx=".9"/><rect x="15" y="14" width="1.8" height="6.5" rx=".9"/><path d="M15.5 10 18.5 5l3 1.3-.6 3.2-3 2.7z"/>';
  var WINGS = '<path d="M12 9C9 5 4 5 1.5 8.5c4-.5 7 .8 10.5 4.3 3.5-3.5 6.5-4.8 10.5-4.3C20 5 15 5 12 9z"/>';
  var CANID = '<path d="M12 21 5.5 14 4 3.5l5 3.8h6l5-3.8L18.5 14z"/>';
  var ICONS = {
    algae: '<path d="M7 21c-3-4 3-6 0-9s2-6 0-9M12 21c-3-4 3-6 0-9s2-6 0-9M17 21c-3-4 3-6 0-9s2-6 0-9"' + S + ' stroke-width="1.8"/>',
    willow: '<path d="M12 21V8"' + S + ' stroke-width="1.8"/><path d="M12 8C8 3.5 2.5 6 3 12M12 8c4-4.5 9.5-2 9 4"' + S + ' stroke-width="1.8"/><path d="M6.2 6.5v8M9 5.2v10M15 5.2v10M17.8 6.5v8"' + S + ' stroke-width="1.3"/>',
    aspen: '<ellipse cx="12" cy="9" rx="5.6" ry="7"/><rect x="11" y="14" width="2" height="7" rx=".6"/>',
    grass: '<path d="M3.5 21 7 6l3.5 15zM8.5 21 12 3l3.5 18zM13.5 21 17 7l3.5 14z"/>',
    sage: '<circle cx="8" cy="15" r="4.6"/><circle cx="16" cy="15" r="4.6"/><circle cx="12" cy="10.5" r="4.8"/><rect x="11" y="16" width="2" height="5" rx=".6"/>',
    whitebark: '<path d="M12 2l6 8h-3l5 7H4l5-7H6z"/><rect x="11" y="17" width="2" height="4"/>',
    mayfly: '<ellipse cx="8.5" cy="8" rx="5" ry="2.4" transform="rotate(-35 8.5 8)"/><ellipse cx="15.5" cy="8" rx="5" ry="2.4" transform="rotate(35 15.5 8)"/><rect x="10.8" y="7" width="2.4" height="10" rx="1.2"/><path d="M12 17 9 22M12 17l3 5"' + S + ' stroke-width="1.2"/>',
    beaver: '<ellipse cx="11" cy="14" rx="6.8" ry="4.8"/><circle cx="17.5" cy="10.5" r="3.5"/><circle cx="16.8" cy="7.3" r="1.2"/><ellipse cx="4" cy="17.5" rx="3.6" ry="1.9" transform="rotate(30 4 17.5)"/><rect x="8" y="17" width="2" height="3.5" rx="1"/><rect x="14" y="16.5" width="2" height="3.5" rx="1"/>',
    moose: '<path d="M12 22c-3.2 0-4.5-3-4.5-6l1.2-4.5h6.6l1.2 4.5c0 3-1.3 6-4.5 6z"/><path d="M8.4 11.5 2 10l1-4.5 4.2 1.6.8-3.4 2.4 2.2zM15.6 11.5 22 10l-1-4.5-4.2 1.6-.8-3.4-2.4 2.2z"/>',
    quad: QUAD,
    elk: QUAD + '<path d="M18.2 5 16 1M18.2 5 20.5 1.5M17.2 3 14.5 2M19.3 3.3 21.5 3"' + S + ' stroke-width="1.4"/>',
    bison: '<ellipse cx="13.5" cy="12.5" rx="7.5" ry="5"/><circle cx="9.5" cy="9.8" r="4.4"/><ellipse cx="5.2" cy="14" rx="3" ry="3.6"/><rect x="9" y="15.5" width="2" height="5.5" rx="1"/><rect x="16.5" y="15.5" width="2" height="5.5" rx="1"/><path d="M3.5 10.5 2 8M6.6 10.3 7 7.8"' + S + ' stroke-width="1.5"/>',
    muledeer: QUAD + '<path d="M18.2 5 17 1.5M18.2 5 21 2.5M17.6 3.2 15.5 2.2"' + S + ' stroke-width="1.4"/>',
    pronghorn: QUAD + '<path d="M18.3 5 18 2.2M18.3 5l2-2"' + S + ' stroke-width="1.5"/>',
    hopper: '<ellipse cx="11" cy="12" rx="7" ry="2.7"/><circle cx="18.5" cy="10.8" r="2.7"/><path d="M8.5 11.5 4.5 4.5 2.5 8M10.5 14l-3 6.5M13.5 14l-1 6.5M19.5 8.5l1.8-3M17.8 8.4l-.8-3"' + S + ' stroke-width="1.4"/>',
    vole: '<ellipse cx="11" cy="14.5" rx="6.8" ry="4.5"/><circle cx="17.8" cy="13.2" r="3.1"/><circle cx="16.2" cy="9.8" r="1.7"/><path d="M4.4 15.5c-2 .2-3 1.8-2.6 4"' + S + ' stroke-width="1.4"/>',
    gsquirrel: '<ellipse cx="11" cy="14.5" rx="4.6" ry="6.2"/><circle cx="14.2" cy="7" r="3.3"/><circle cx="12.6" cy="4.2" r="1.3"/><path d="M6.5 18c-3 0-4.5-2-4-5"' + S + ' stroke-width="1.6"/><ellipse cx="8" cy="20.5" rx="2" ry="1"/>',
    rsquirrel: '<ellipse cx="7" cy="11" rx="4.5" ry="8" transform="rotate(-15 7 11)"/><ellipse cx="14" cy="15" rx="4" ry="5"/><circle cx="16" cy="9" r="3"/><circle cx="14.5" cy="6.4" r="1.1"/>',
    otter: '<ellipse cx="11" cy="14.5" rx="8.5" ry="3.2" transform="rotate(-12 11 14.5)"/><circle cx="19" cy="9.8" r="3.1"/><circle cx="17.6" cy="6.9" r="1.1"/><path d="M3 17.5c-1.3 1-1.8 2.6-1 4"' + S + ' stroke-width="1.8"/><rect x="7" y="16" width="1.8" height="3.5" rx=".9"/><rect x="13" y="15.5" width="1.8" height="3.5" rx=".9"/>',
    trout: '<path d="M2.5 12c3.2-5 9.5-6 14.5-3l4.5-3.5v13L17 15c-5 3-11.3 2-14.5-3z"/>',
    osprey: WINGS + '<ellipse cx="12" cy="13.5" rx="1.9" ry="3.4"/><path d="M9.5 20.5c1-1.6 3.5-1.6 5 0-1.5 1.6-4 1.6-5 0z"/>',
    baldeagle: WINGS + '<ellipse cx="12" cy="14" rx="1.9" ry="4"/><circle cx="12" cy="7.5" r="2.3"/><path d="M13.8 7.4 16 8.4l-2.2.9z"/>',
    raven: '<ellipse cx="11" cy="12" rx="6" ry="4" transform="rotate(-20 11 12)"/><circle cx="17" cy="8" r="3"/><path d="M19.5 8.3 23 9.2l-3.3 1z"/><path d="M5.5 15 2 19l5-1z"/><path d="M10 16v5M13 15.5v5.5"' + S + ' stroke-width="1.3"/>',
    coyote: CANID,
    fox: '<path d="M12 21 8 14.5 4 3.5l5 3.8h6l5-3.8-4 11z"/>',
    meadowlark: '<ellipse cx="12" cy="13" rx="5.5" ry="4.5"/><circle cx="16.5" cy="8.5" r="2.8"/><path d="M19 8.5l3.5 1-3.5 1z"/><path d="M7 15 2 20l6-2z"/><path d="M11 17.5v3.5M14 17v4"' + S + ' stroke-width="1.3"/>',
    hawk: WINGS + '<ellipse cx="12" cy="13" rx="1.9" ry="3.3"/><path d="M9.5 21 12 17l2.5 4z"/>',
    goldeneagle: '<path d="M12 9C8.5 4.5 3.5 4.6 1 8.6l3.2-.4-2 1.7 3.7-.5-1.7 2C9 10.2 10.6 11 12 12.8c1.4-1.8 3-2.6 6.1-1.4l-1.7-2 3.7.5-2-1.7 3.2.4C20.5 4.6 15.5 4.5 12 9z"/><ellipse cx="12" cy="14.5" rx="1.9" ry="4"/>',
    wolf: CANID + '<path d="M5.5 14 2 15l3 2zM18.5 14l3.5 1-3 2z"/>',
    grizzly: '<circle cx="12" cy="13" r="8"/><circle cx="6" cy="6" r="2.8"/><circle cx="18" cy="6" r="2.8"/><ellipse cx="12" cy="15.5" rx="3.4" ry="2.6" fill-opacity=".35"/>',
    lion: '<path d="M12 21c-5 0-8-3-8-7 0-2 .6-3.5 1.4-4.8L5 3.5l4.6 3C10.4 6.2 11.2 6 12 6s1.6.2 2.4.5l4.6-3-.4 5.7C19.4 10.5 20 12 20 14c0 4-3 7-8 7z"/>',
    elephant: '<ellipse cx="11.5" cy="11" rx="7.5" ry="5"/><rect x="5" y="13.5" width="2.4" height="7.5" rx="1"/><rect x="9" y="14" width="2.4" height="7" rx="1"/><rect x="13.2" y="14" width="2.4" height="7" rx="1"/><rect x="16.5" y="13.5" width="2.4" height="7.5" rx="1"/><circle cx="19" cy="8.5" r="3.4"/><path d="M21.3 10.5c1.4 2 1 5.5-1.2 7"' + S + ' stroke-width="2"/><ellipse cx="16.8" cy="9" rx="1.8" ry="3" fill-opacity=".4"/>',
    giraffe: '<ellipse cx="9" cy="14.5" rx="5.5" ry="3.4"/><rect x="4.5" y="16.5" width="1.8" height="5" rx=".8"/><rect x="7" y="17" width="1.8" height="4.5" rx=".8"/><rect x="10.5" y="17" width="1.8" height="4.5" rx=".8"/><rect x="12.5" y="16.5" width="1.8" height="5" rx=".8"/><path d="M11.5 12.5 15.5 3.5l2.3 1-2.8 8.5z"/><ellipse cx="18" cy="4" rx="3" ry="1.8" transform="rotate(-15 18 4)"/><path d="M16 2.2V.8M18 1.8V.5"' + S + ' stroke-width="1.2"/>',
    croc: '<ellipse cx="11" cy="13" rx="9" ry="2.8"/><path d="M19 11.2 23 11l-.2 3-3.8-.4z"/><rect x="6" y="14.5" width="2" height="3.5" rx=".8"/><rect x="13" y="14.5" width="2" height="3.5" rx=".8"/><path d="M2.5 12.5c-1.5.5-1.8 2.2-.5 3.5"' + S + ' stroke-width="1.6"/>',
    snake: '<path d="M4 19c5 0 6-4 1.5-5.2S5.5 7 11 7c4.5 0 6 3 9 3"' + S + ' stroke-width="3"/><circle cx="20.5" cy="10" r="2"/>',
    turtle: '<ellipse cx="11" cy="12" rx="7" ry="5"/><circle cx="19.5" cy="11.5" r="2.5"/><ellipse cx="6" cy="17" rx="3" ry="1.5" transform="rotate(30 6 17)"/><ellipse cx="14" cy="17.5" rx="3" ry="1.4"/>',
    coral: '<path d="M12 21V12M12 15 7 9M12 12 17 6M7 9 4 5M7 9 8 4M17 6l3-1M17 6l-1-4"' + S + ' stroke-width="2.4"/>',
    shark: '<path d="M2 14c5-5 12-6 18-2l2-3v10l-2-3c-6 3-13 2-18-2z"/><path d="M10 9 13 4l2 5z"/>',
    starfish: '<path d="M12 2l2.6 6.8 7.4.4-5.7 4.6 1.9 7.2L12 17l-6.2 4 1.9-7.2L2 9.2l7.4-.4z"/>',
    seal: '<ellipse cx="11" cy="14" rx="8" ry="4"/><circle cx="19" cy="10.5" r="3"/><path d="M3 17l-2 3 5-1z"/><path d="M10 17l-1 3.5 3-1.5z"/>',
    whale: '<ellipse cx="11" cy="13" rx="9" ry="4.5"/><path d="M19 12 23 8v8z"/>',
    ant: '<circle cx="6" cy="14" r="2.5"/><circle cx="11.5" cy="13" r="2"/><ellipse cx="17.5" cy="12" rx="3.2" ry="2.4"/><path d="M8 15 6 20M11 15l-1 5M13 14l2 6M19 10l2-4M17 10l-1-4"' + S + ' stroke-width="1.2"/>',
    shell: '<path d="M12 3C7 3 4 8 6 13c1 3 4 5 8 4s5-5 3-8c-1.5-2-4-2-5.5-.5s-1 3 1 3"' + S + ' stroke-width="2"/>',
    rain: '<path d="M7 14a4.5 4.5 0 0 1 .5-9 5.5 5.5 0 0 1 10.3 1.5A3.8 3.8 0 0 1 17 14z"/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3"' + S + ' stroke-width="1.6"/>',
    ice: '<path d="M12 2v20M3.3 7 20.7 17M3.3 17 20.7 7"' + S + ' stroke-width="2"/>',
    water: '<path d="M12 3C8 9 6 12 6 15a6 6 0 0 0 12 0c0-3-2-6-6-12z"/>',
    sun: '<circle cx="12" cy="12" r="4.5"/><path d="M12 2v3.5M12 18.5V22M2 12h3.5M18.5 12H22M4.9 4.9l2.5 2.5M16.6 16.6l2.5 2.5M19.1 4.9l-2.5 2.5M7.4 16.6l-2.5 2.5"' + S + ' stroke-width="1.8"/>',
    soil: '<path d="M3 8c3-2 6 2 9 0s6-2 9 0v3H3z"/><rect x="3" y="12.5" width="18" height="3.2" rx="1"/><rect x="3" y="17" width="18" height="3.2" rx="1"/>',
    decomp: '<path d="M3 12a9 8 0 0 1 18 0z"/><path d="M9.5 12.5h5l-.8 8h-3.4z"/>',
    fire: '<path d="M12 2c1 4 5 6 5 11a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-4-1-6 1-10z"/>'
  };

  var DATA = R[1] && R[1].cross ? R[1] : { couple: 0.5, src: {}, cross: [] };   /* from the head loader (api/journeys); with no file the app starts with no journeys */
  var ABOUT = {}, ABOUT_P = {};   /* species id -> description text, or null when there is none; filled one species at a time */
  function aboutLink(n) { return ' <a href="https://en.wikipedia.org/wiki/' + encodeURIComponent((n.wiki || n.latin).replace(/ /g, "_")) + '" target="_blank" rel="noopener">Wikipedia</a>'; }
  function sidOf(n) { return n.latin.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, ""); }   /* the same id the build gives the species (build/species.py slug) */
  function aboutText(n) { var t = ABOUT[sidOf(n)]; return t ? t.replace(/&/g, "&amp;").replace(/</g, "&lt;") + aboutLink(n) : ""; }
