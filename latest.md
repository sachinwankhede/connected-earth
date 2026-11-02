# Site speed, 2026-11-02 18:25 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 182 | n/a |  |
| map: map style and index, last answer (ms) | 396 | n/a |  |
| map: map style and index, requests | 1 | n/a |  |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 4032 | n/a |  |
| map: map glyphs, last answer (ms) | 5068 | n/a |  |
| map: map glyphs, requests | 1 | n/a |  |
| map: satellite tiles, first request (ms) | 3617 | n/a |  |
| map: satellite tiles, last answer (ms) | 4797 | n/a |  |
| map: satellite tiles, requests | 12 | n/a |  |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 397 | 428 | -7% |
| page loaded (ms) | 3576 | 5358 | -33% |
| map drawn (ms) | 5451 | 6854 | -20% |
| blocked before map (ms) | 719 | 1691 | -57% |
| download (KB) | 1078 | 1226 | -12% |
| requests | 26 | 25 | +4% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 97 | 159 | -39% |
| tap: filter on blocked (ms) | 18 | 151 | -88% |
| tap: filter off (ms) | 96 | 149 | -36% |
| tap: filter off blocked (ms) | 21 | 141 | -85% |
| tap: state parks on (ms) | 114 | 577 | -80% |
| tap: state parks on blocked (ms) | 33 | 164 | -80% |
| tap: state parks off (ms) | 90 | 262 | -66% |
| tap: state parks off blocked (ms) | 15 | 151 | -90% |
| tap: open place (ms) | 29 | 46 | -37% |
| tap: open place blocked (ms) | 39 | 76 | -49% |
| tap: back from place (ms) | 235 | 338 | -30% |
| tap: back from place blocked (ms) | 123 | 270 | -54% |
| tap: journeys tab (ms) | 29 | 65 | -55% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 236 | 326 | -28% |
| tap: open journey blocked (ms) | 0 | 8 | -100% |
| tap: back from journey (ms) | 148 | 287 | -48% |
| tap: back from journey blocked (ms) | 44 | 172 | -74% |

By host: sachinwankhede.github.io 36 req / 1584 KB; thumb.wikimedia.org 45 req / 362 KB; server.arcgisonline.com 28 req / 132 KB; tiles.openfreemap.org 4 req / 48 KB;  8 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 3174 | 3329 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 3175 | 3329 | Navigation Timing |
| Load event | 5 | 0 | 3576 | 3721 | Navigation Timing |
| First contentful paint | 5 | 0 | 397 | 605 | Paint Timing |
| App data ready | 5 | 0 | 3177 | 3323 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 3177 | 3323 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3575 | 3712 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 4042 | 4177 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 5451 | 5615 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 5450 | 5615 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5898 | 6065 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5911 | 6088 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 12/13; total duration 1331/1363 ms; blocking time over 50 ms 719/737 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 113 | 123 |
| DOM interactive | 790 | 815 |
| Load event | 793 | 819 |
| Map loaded | 1798 | 1880 |
| Blocking time before map loaded | 754 | 780 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 1158 | 1165 |
| place warm open | 5 | 190 | 208 |
| place first picture arrived | 5 | 1270 | 1276 |
| place last picture arrived | 5 | 4846 | 4848 |
| food-web cold open | 5 | 2112 | 2119 |
| food-web warm open | 5 | 438 | 443 |
| species selection | 5 | 114 | 135 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 2 | 165 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 39 | 505 |
| food-web cold open | web data | 2 | 165 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | none recorded | 0 | 0 |

## desktop

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 25 | n/a |  |
| map: map style and index, last answer (ms) | 74 | n/a |  |
| map: map style and index, requests | 1 | n/a |  |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 537 | n/a |  |
| map: map glyphs, last answer (ms) | 563 | n/a |  |
| map: map glyphs, requests | 1 | n/a |  |
| map: satellite tiles, first request (ms) | 268 | n/a |  |
| map: satellite tiles, last answer (ms) | 302 | n/a |  |
| map: satellite tiles, requests | 16 | n/a |  |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 155 | 133 | +16% ⚠ |
| page loaded (ms) | 255 | 564 | -55% |
| map drawn (ms) | 1183 | 1600 | -26% |
| blocked before map (ms) | 395 | 740 | -47% |
| download (KB) | 2599 | 2802 | -7% |
| requests | 65 | 68 | -4% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 102 | 138 | -26% |
| tap: filter on blocked (ms) | 219 | 379 | -42% |
| tap: filter off (ms) | 110 | 139 | -21% |
| tap: filter off blocked (ms) | 258 | 361 | -29% |
| tap: state parks on (ms) | 252 | 358 | -30% |
| tap: state parks on blocked (ms) | 186 | 308 | -40% |
| tap: state parks off (ms) | 176 | 213 | -17% |
| tap: state parks off blocked (ms) | 155 | 267 | -42% |
| tap: open place (ms) | 12 | 15 | -20% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 230 | 314 | -27% |
| tap: back from place blocked (ms) | 279 | 414 | -33% |
| tap: journeys tab (ms) | 24 | 16 | +50% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 57 | 78 | -27% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 135 | 257 | -47% |
| tap: back from journey blocked (ms) | 188 | 385 | -51% |

By host: sachinwankhede.github.io 162 req / 3943 KB; thumb.wikimedia.org 46 req / 365 KB; server.arcgisonline.com 40 req / 175 KB; tiles.openfreemap.org 4 req / 48 KB;  8 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 141 | 149 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 141 | 149 | Navigation Timing |
| Load event | 5 | 0 | 255 | 258 | Navigation Timing |
| First contentful paint | 5 | 0 | 155 | 160 | Paint Timing |
| App data ready | 5 | 0 | 129 | 138 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 129 | 138 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 256 | 259 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 286 | 292 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1183 | 1784 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1183 | 1784 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1207 | 1799 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1243 | 1823 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/16; total duration 891/1369 ms; blocking time over 50 ms 413/589 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 58 | 66 |
| DOM interactive | 159 | 165 |
| Load event | 262 | 273 |
| Map loaded | 1099 | 1226 |
| Blocking time before map loaded | 329 | 408 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 55 | 57 |
| place warm open | 5 | 121 | 123 |
| place first picture arrived | 5 | 52 | 58 |
| place last picture arrived | 5 | 283 | 284 |
| food-web cold open | 5 | 171 | 174 |
| food-web warm open | 5 | 163 | 187 |
| species selection | 5 | 25 | 26 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 2 | 165 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 40 | 537 |
| food-web cold open | web data | 2 | 165 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 1 | 0 |
