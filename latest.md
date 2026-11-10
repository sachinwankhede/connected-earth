# Site speed, 2026-11-10 16:26 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 181 | 189 | -4% |
| map: map style and index, last answer (ms) | 454 | 465 | -2% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3899 | 3571 | +9% |
| map: map glyphs, last answer (ms) | 4279 | 4167 | +3% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3364 | 3239 | +4% |
| map: satellite tiles, last answer (ms) | 3777 | 3716 | +2% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 423 | 422 | +0% |
| page loaded (ms) | 3321 | 3206 | +4% |
| map drawn (ms) | 4757 | 4475 | +6% |
| blocked before map (ms) | 1074 | 683 | +57% ⚠ |
| download (KB) | 786 | 786 | +0% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 138 | 101 | +37% ⚠ |
| tap: filter on blocked (ms) | 127 | 44 | +189% ⚠ |
| tap: filter off (ms) | 116 | 88 | +32% ⚠ |
| tap: filter off blocked (ms) | 155 | 45 | +244% ⚠ |
| tap: state parks on (ms) | 122 | 99 | +23% ⚠ |
| tap: state parks on blocked (ms) | 241 | 125 | +93% ⚠ |
| tap: state parks off (ms) | 130 | 105 | +24% ⚠ |
| tap: state parks off blocked (ms) | 103 | 35 | +194% ⚠ |
| tap: open place (ms) | 32 | 29 | +10% |
| tap: open place blocked (ms) | 78 | 36 | +117% ⚠ |
| tap: back from place (ms) | 296 | 236 | +25% ⚠ |
| tap: back from place blocked (ms) | 261 | 161 | +62% ⚠ |
| tap: journeys tab (ms) | 40 | 31 | +29% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 279 | 215 | +30% ⚠ |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 172 | 142 | +21% ⚠ |
| tap: back from journey blocked (ms) | 124 | 59 | +110% ⚠ |
| tap: search ma (cold) (ms) | 90 | 89 | +1% |
| tap: search ma (cold) blocked (ms) | 303 | 145 | +109% ⚠ |
| tap: search mar (ms) | 91 | 140 | -35% |
| tap: search mar blocked (ms) | 251 | 108 | +132% ⚠ |
| tap: search mari (ms) | 134 | 107 | +25% ⚠ |
| tap: search mari blocked (ms) | 250 | 88 | +184% ⚠ |
| tap: search osprey (ms) | 81 | 68 | +19% |
| tap: search osprey blocked (ms) | 238 | 81 | +194% ⚠ |

By host: sachinwankhede.github.io 131 req / 1714 KB; server.arcgisonline.com 16 req / 95 KB; tiles.openfreemap.org 7 req / 91 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2450 | 2453 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2450 | 2453 | Navigation Timing |
| Load event | 5 | 0 | 3321 | 3437 | Navigation Timing |
| First contentful paint | 5 | 0 | 423 | 570 | Paint Timing |
| App data ready | 5 | 0 | 2453 | 2456 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2453 | 2457 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3322 | 3441 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3692 | 3791 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4757 | 5036 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4757 | 5128 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5879 | 6256 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5900 | 6284 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 15/16; total duration 1808/2090 ms; blocking time over 50 ms 1074/1300 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 142. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 157 | 168 |
| DOM interactive | 895 | 938 |
| Load event | 899 | 942 |
| Map loaded | 2152 | 2165 |
| Blocking time before map loaded | 1050 | 1083 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 392 | 402 |
| place warm open | 5 | 225 | 231 |
| place first picture arrived | 5 | 521 | 542 |
| place last picture arrived | 5 | 1376 | 1391 |
| food-web cold open | 5 | 1567 | 1601 |
| food-web warm open | 5 | 604 | 664 |
| species selection | 5 | 196 | 207 |

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
| map: map style and index, first request (ms) | 23 | 35 | -34% |
| map: map style and index, last answer (ms) | 60 | 90 | -34% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 697 | 569 | +23% ⚠ |
| map: map glyphs, last answer (ms) | 713 | 606 | +18% ⚠ |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 322 | 272 | +18% ⚠ |
| map: satellite tiles, last answer (ms) | 342 | 288 | +19% ⚠ |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 87 | 89 | -2% |
| page loaded (ms) | 309 | 264 | +17% ⚠ |
| map drawn (ms) | 1444 | 1183 | +22% ⚠ |
| blocked before map (ms) | 610 | 407 | +50% ⚠ |
| download (KB) | 2238 | 2237 | +0% |
| requests | 54 | 54 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 135 | 107 | +26% ⚠ |
| tap: filter on blocked (ms) | 373 | 251 | +49% ⚠ |
| tap: filter off (ms) | 142 | 117 | +21% ⚠ |
| tap: filter off blocked (ms) | 371 | 311 | +19% ⚠ |
| tap: state parks on (ms) | 121 | 100 | +21% ⚠ |
| tap: state parks on blocked (ms) | 589 | 454 | +30% ⚠ |
| tap: state parks off (ms) | 218 | 183 | +19% ⚠ |
| tap: state parks off blocked (ms) | 265 | 176 | +51% ⚠ |
| tap: open place (ms) | 16 | 14 | +14% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 212 | 175 | +21% ⚠ |
| tap: back from place blocked (ms) | 329 | 262 | +26% ⚠ |
| tap: journeys tab (ms) | 16 | 13 | +23% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 71 | 53 | +34% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 167 | 143 | +17% ⚠ |
| tap: back from journey blocked (ms) | 266 | 182 | +46% ⚠ |
| tap: search ma (cold) (ms) | 111 | 95 | +17% |
| tap: search ma (cold) blocked (ms) | 503 | 395 | +27% ⚠ |
| tap: search mar (ms) | 129 | 104 | +24% ⚠ |
| tap: search mar blocked (ms) | 499 | 392 | +27% ⚠ |
| tap: search mari (ms) | 131 | 107 | +22% ⚠ |
| tap: search mari blocked (ms) | 577 | 454 | +27% ⚠ |
| tap: search osprey (ms) | 144 | 112 | +29% ⚠ |
| tap: search osprey blocked (ms) | 559 | 473 | +18% ⚠ |

By host: sachinwankhede.github.io 333 req / 4472 KB; server.arcgisonline.com 61 req / 508 KB; tiles.openfreemap.org 8 req / 131 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 64 | 65 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 64 | 66 | Navigation Timing |
| Load event | 5 | 0 | 309 | 318 | Navigation Timing |
| First contentful paint | 5 | 0 | 87 | 94 | Paint Timing |
| App data ready | 5 | 0 | 171 | 178 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 171 | 178 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 310 | 319 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 341 | 399 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1444 | 1474 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1444 | 1474 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1504 | 1557 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1536 | 1604 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 11/11; total duration 1149/1163 ms; blocking time over 50 ms 610/657 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 79 | 82 |
| DOM interactive | 176 | 181 |
| Load event | 319 | 324 |
| Map loaded | 1403 | 1468 |
| Blocking time before map loaded | 606 | 611 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 92 | 92 |
| place warm open | 5 | 86 | 153 |
| place first picture arrived | 5 | 51 | 55 |
| place last picture arrived | 5 | 95 | 110 |
| food-web cold open | 5 | 210 | 228 |
| food-web warm open | 5 | 213 | 215 |
| species selection | 5 | 46 | 61 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 30 | 57 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 36 | 163 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 17 | 34 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 4 |
