# Site speed, 2026-11-09 18:50 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 189 | 201 | -6% |
| map: map style and index, last answer (ms) | 465 | 485 | -4% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3571 | 3632 | -2% |
| map: map glyphs, last answer (ms) | 4167 | 4183 | 0% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3239 | 3216 | +1% |
| map: satellite tiles, last answer (ms) | 3716 | 3747 | -1% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 422 | 445 | -5% |
| page loaded (ms) | 3206 | 3185 | +1% |
| map drawn (ms) | 4475 | 4578 | -2% |
| blocked before map (ms) | 683 | 631 | +8% |
| download (KB) | 786 | 790 | 0% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 101 | 95 | +6% |
| tap: filter on blocked (ms) | 44 | 36 | +22% |
| tap: filter off (ms) | 88 | 92 | -4% |
| tap: filter off blocked (ms) | 45 | 54 | -17% |
| tap: state parks on (ms) | 99 | 97 | +2% |
| tap: state parks on blocked (ms) | 125 | 104 | +20% ⚠ |
| tap: state parks off (ms) | 105 | 94 | +12% |
| tap: state parks off blocked (ms) | 35 | 27 | +30% |
| tap: open place (ms) | 29 | 23 | +26% |
| tap: open place blocked (ms) | 36 | 33 | +9% |
| tap: back from place (ms) | 236 | 234 | +1% |
| tap: back from place blocked (ms) | 161 | 161 | 0% |
| tap: journeys tab (ms) | 31 | 29 | +7% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 215 | 200 | +8% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 142 | 131 | +8% |
| tap: back from journey blocked (ms) | 59 | 50 | +18% |
| tap: search ma (cold) (ms) | 89 | 82 | +9% |
| tap: search ma (cold) blocked (ms) | 145 | 133 | +9% |
| tap: search mar (ms) | 140 | 125 | +12% |
| tap: search mar blocked (ms) | 108 | 82 | +32% ⚠ |
| tap: search mari (ms) | 107 | 103 | +4% |
| tap: search mari blocked (ms) | 88 | 64 | +38% ⚠ |
| tap: search osprey (ms) | 68 | 66 | +3% |
| tap: search osprey blocked (ms) | 81 | 61 | +33% |

By host: sachinwankhede.github.io 131 req / 1713 KB; server.arcgisonline.com 16 req / 95 KB; tiles.openfreemap.org 7 req / 91 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2427 | 2952 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2427 | 2952 | Navigation Timing |
| Load event | 5 | 0 | 3206 | 3951 | Navigation Timing |
| First contentful paint | 5 | 0 | 422 | 1286 | Paint Timing |
| App data ready | 5 | 0 | 2425 | 2953 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2425 | 2953 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3208 | 3953 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3687 | 4364 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4475 | 5222 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4475 | 5221 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5611 | 6892 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5628 | 6910 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 14/15; total duration 1359/1423 ms; blocking time over 50 ms 683/706 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 148. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 142 | 202 |
| DOM interactive | 704 | 754 |
| Load event | 707 | 757 |
| Map loaded | 1683 | 1741 |
| Blocking time before map loaded | 686 | 719 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 338 | 364 |
| place warm open | 5 | 179 | 219 |
| place first picture arrived | 5 | 497 | 516 |
| place last picture arrived | 5 | 1351 | 1623 |
| food-web cold open | 5 | 1399 | 1571 |
| food-web warm open | 5 | 469 | 524 |
| species selection | 5 | 158 | 171 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 36 | 163 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | none recorded | 0 | 0 |

## desktop

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 35 | 46 | -23% |
| map: map style and index, last answer (ms) | 90 | 97 | -8% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 569 | 664 | -14% |
| map: map glyphs, last answer (ms) | 606 | 687 | -12% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 272 | 281 | -3% |
| map: satellite tiles, last answer (ms) | 288 | 328 | -12% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 89 | 97 | -8% |
| page loaded (ms) | 264 | 273 | -3% |
| map drawn (ms) | 1183 | 1240 | -5% |
| blocked before map (ms) | 407 | 420 | -3% |
| download (KB) | 2237 | 2344 | -5% |
| requests | 54 | 58 | -7% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 107 | 107 | 0% |
| tap: filter on blocked (ms) | 251 | 254 | -1% |
| tap: filter off (ms) | 117 | 115 | +2% |
| tap: filter off blocked (ms) | 311 | 309 | +1% |
| tap: state parks on (ms) | 100 | 99 | +1% |
| tap: state parks on blocked (ms) | 454 | 441 | +3% |
| tap: state parks off (ms) | 183 | 181 | +1% |
| tap: state parks off blocked (ms) | 176 | 174 | +1% |
| tap: open place (ms) | 14 | 14 | 0% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 175 | 167 | +5% |
| tap: back from place blocked (ms) | 262 | 262 | 0% |
| tap: journeys tab (ms) | 13 | 13 | 0% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 53 | 52 | +2% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 143 | 140 | +2% |
| tap: back from journey blocked (ms) | 182 | 178 | +2% |
| tap: search ma (cold) (ms) | 95 | 91 | +4% |
| tap: search ma (cold) blocked (ms) | 395 | 397 | -1% |
| tap: search mar (ms) | 104 | 104 | 0% |
| tap: search mar blocked (ms) | 392 | 387 | +1% |
| tap: search mari (ms) | 107 | 106 | +1% |
| tap: search mari blocked (ms) | 454 | 448 | +1% |
| tap: search osprey (ms) | 112 | 106 | +6% |
| tap: search osprey blocked (ms) | 473 | 468 | +1% |

By host: sachinwankhede.github.io 333 req / 4472 KB; server.arcgisonline.com 66 req / 509 KB; tiles.openfreemap.org 8 req / 131 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 63 | 64 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 64 | 64 | Navigation Timing |
| Load event | 5 | 0 | 264 | 269 | Navigation Timing |
| First contentful paint | 5 | 0 | 89 | 90 | Paint Timing |
| App data ready | 5 | 0 | 153 | 156 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 153 | 156 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 265 | 312 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 288 | 322 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1183 | 1211 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1183 | 1211 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1231 | 1259 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1268 | 1298 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 9/9; total duration 857/871 ms; blocking time over 50 ms 407/421 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 144. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 64 | 66 |
| DOM interactive | 138 | 149 |
| Load event | 252 | 260 |
| Map loaded | 1174 | 1194 |
| Blocking time before map loaded | 401 | 412 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 66 | 69 |
| place warm open | 5 | 114 | 141 |
| place first picture arrived | 5 | 43 | 53 |
| place last picture arrived | 5 | 65 | 81 |
| food-web cold open | 5 | 166 | 167 |
| food-web warm open | 5 | 121 | 213 |
| species selection | 5 | 48 | 49 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 36 | 163 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 36 | 163 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 0 | 0 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 1 | 1 |
