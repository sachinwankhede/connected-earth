# Site speed, 2026-11-06 15:56 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 183 | 203 | -10% |
| map: map style and index, last answer (ms) | 418 | 411 | +2% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3492 | 3900 | -10% |
| map: map glyphs, last answer (ms) | 4101 | 4280 | -4% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3180 | 3334 | -5% |
| map: satellite tiles, last answer (ms) | 3673 | 3746 | -2% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 415 | 445 | -7% |
| page loaded (ms) | 3152 | 3292 | -4% |
| map drawn (ms) | 4386 | 4822 | -9% |
| blocked before map (ms) | 486 | 1109 | -56% |
| download (KB) | 790 | 789 | +0% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 78 | 126 | -38% |
| tap: filter on blocked (ms) | 0 | 249 | -100% |
| tap: filter off (ms) | 72 | 121 | -40% |
| tap: filter off blocked (ms) | 0 | 261 | -100% |
| tap: state parks on (ms) | 77 | 131 | -41% |
| tap: state parks on blocked (ms) | 4 | 349 | -99% |
| tap: state parks off (ms) | 83 | 139 | -40% |
| tap: state parks off blocked (ms) | 0 | 172 | -100% |
| tap: open place (ms) | 25 | 29 | -14% |
| tap: open place blocked (ms) | 20 | 55 | -64% |
| tap: back from place (ms) | 188 | 324 | -42% |
| tap: back from place blocked (ms) | 92 | 368 | -75% |
| tap: journeys tab (ms) | 26 | 39 | -33% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 180 | 272 | -34% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 111 | 191 | -42% |
| tap: back from journey blocked (ms) | 18 | 227 | -92% |
| tap: search ma (cold) (ms) | 73 | 108 | -32% |
| tap: search ma (cold) blocked (ms) | 50 | 368 | -86% |
| tap: search mar (ms) | 119 | 102 | +17% |
| tap: search mar blocked (ms) | 5 | 360 | -99% |
| tap: search mari (ms) | 90 | 171 | -47% |
| tap: search mari blocked (ms) | 0 | 370 | -100% |
| tap: search osprey (ms) | 55 | 98 | -44% |
| tap: search osprey blocked (ms) | 0 | 370 | -100% |

By host: sachinwankhede.github.io 135 req / 1775 KB; server.arcgisonline.com 16 req / 95 KB; tiles.openfreemap.org 7 req / 91 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2399 | 2401 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2400 | 2401 | Navigation Timing |
| Load event | 5 | 0 | 3152 | 3199 | Navigation Timing |
| First contentful paint | 5 | 0 | 415 | 466 | Paint Timing |
| App data ready | 5 | 0 | 2398 | 2402 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2398 | 2402 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3148 | 3195 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3530 | 3548 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4386 | 4421 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4403 | 4420 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5585 | 5594 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5603 | 5613 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/10; total duration 973/1006 ms; blocking time over 50 ms 495/506 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 124 | 154 |
| DOM interactive | 594 | 659 |
| Load event | 598 | 663 |
| Map loaded | 1470 | 1556 |
| Blocking time before map loaded | 504 | 576 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 309 | 322 |
| place warm open | 5 | 160 | 189 |
| place first picture arrived | 5 | 477 | 484 |
| place last picture arrived | 5 | 1354 | 1360 |
| food-web cold open | 5 | 1241 | 1272 |
| food-web warm open | 5 | 294 | 362 |
| species selection | 5 | 131 | 140 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 37 | 165 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | none recorded | 0 | 0 |

## desktop

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 20 | 59 | -66% |
| map: map style and index, last answer (ms) | 50 | 83 | -40% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 608 | 741 | -18% |
| map: map glyphs, last answer (ms) | 640 | 757 | -16% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 242 | 345 | -30% |
| map: satellite tiles, last answer (ms) | 259 | 362 | -28% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 67 | 127 | -47% |
| page loaded (ms) | 228 | 334 | -32% |
| map drawn (ms) | 999 | 1531 | -35% |
| blocked before map (ms) | 263 | 694 | -62% |
| download (KB) | 2344 | 2267 | +3% |
| requests | 58 | 55 | +5% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 87 | 162 | -46% |
| tap: filter on blocked (ms) | 123 | 431 | -71% |
| tap: filter off (ms) | 96 | 167 | -43% |
| tap: filter off blocked (ms) | 146 | 498 | -71% |
| tap: state parks on (ms) | 81 | 151 | -46% |
| tap: state parks on blocked (ms) | 295 | 690 | -57% |
| tap: state parks off (ms) | 139 | 248 | -44% |
| tap: state parks off blocked (ms) | 80 | 332 | -76% |
| tap: open place (ms) | 12 | 13 | -8% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 147 | 261 | -44% |
| tap: back from place blocked (ms) | 124 | 559 | -78% |
| tap: journeys tab (ms) | 12 | 15 | -20% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 53 | 70 | -24% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 117 | 203 | -42% |
| tap: back from journey blocked (ms) | 107 | 382 | -72% |
| tap: search ma (cold) (ms) | 71 | 140 | -49% |
| tap: search ma (cold) blocked (ms) | 243 | 633 | -62% |
| tap: search mar (ms) | 89 | 178 | -50% |
| tap: search mar blocked (ms) | 219 | 655 | -67% |
| tap: search mari (ms) | 78 | 170 | -54% |
| tap: search mari blocked (ms) | 289 | 653 | -56% |
| tap: search osprey (ms) | 87 | 135 | -36% |
| tap: search osprey blocked (ms) | 323 | 651 | -50% |

By host: sachinwankhede.github.io 354 req / 4750 KB; server.arcgisonline.com 71 req / 555 KB; tiles.openfreemap.org 8 req / 131 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 45 | 48 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 45 | 48 | Navigation Timing |
| Load event | 5 | 0 | 228 | 245 | Navigation Timing |
| First contentful paint | 5 | 0 | 67 | 71 | Paint Timing |
| App data ready | 5 | 0 | 128 | 135 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 128 | 135 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 239 | 278 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 257 | 271 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 999 | 1029 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1021 | 1046 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1067 | 1095 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1102 | 1133 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 9/9; total duration 724/743 ms; blocking time over 50 ms 274/293 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 144. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 72 | 87 |
| DOM interactive | 63 | 120 |
| Load event | 240 | 246 |
| Map loaded | 1060 | 1074 |
| Blocking time before map loaded | 270 | 281 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 54 | 61 |
| place warm open | 5 | 47 | 114 |
| place first picture arrived | 5 | 40 | 41 |
| place last picture arrived | 5 | 67 | 68 |
| food-web cold open | 5 | 166 | 231 |
| food-web warm open | 5 | 126 | 149 |
| species selection | 5 | 28 | 35 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 20 | 39 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 38 | 198 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 34 | 65 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 4 |
