# Site speed, 2026-11-04 16:21 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 174 | 176 | -1% |
| map: map style and index, last answer (ms) | 424 | 492 | -14% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3795 | 4031 | -6% |
| map: map glyphs, last answer (ms) | 4280 | 4874 | -12% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3294 | 3526 | -7% |
| map: satellite tiles, last answer (ms) | 3830 | 4573 | -16% |
| map: satellite tiles, requests | 4 | 12 | -67% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 417 | 415 | +0% |
| page loaded (ms) | 3254 | 3451 | -6% |
| map drawn (ms) | 4584 | 5322 | -14% |
| blocked before map (ms) | 988 | 1015 | -3% |
| download (KB) | 782 | 877 | -11% |
| requests | 20 | 27 | -26% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 126 | 106 | +19% |
| tap: filter on blocked (ms) | 107 | 115 | -7% |
| tap: filter off (ms) | 112 | 104 | +8% |
| tap: filter off blocked (ms) | 147 | 134 | +10% |
| tap: state parks on (ms) | 120 | 115 | +4% |
| tap: state parks on blocked (ms) | 217 | 246 | -12% |
| tap: state parks off (ms) | 125 | 121 | +3% |
| tap: state parks off blocked (ms) | 109 | 90 | +21% |
| tap: open place (ms) | 27 | 29 | -7% |
| tap: open place blocked (ms) | 58 | 56 | +4% |
| tap: back from place (ms) | 287 | 268 | +7% |
| tap: back from place blocked (ms) | 261 | 256 | +2% |
| tap: journeys tab (ms) | 39 | 37 | +5% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 261 | 266 | -2% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 164 | 165 | -1% |
| tap: back from journey blocked (ms) | 121 | 126 | -4% |
| tap: search ma (cold) (ms) | 173 | 172 | +1% |
| tap: search ma (cold) blocked (ms) | 230 | 246 | -7% |
| tap: search mar (ms) | 149 | 158 | -6% |
| tap: search mar blocked (ms) | 236 | 227 | +4% |
| tap: search mari (ms) | 171 | 176 | -3% |
| tap: search mari blocked (ms) | 234 | 249 | -6% |
| tap: search osprey (ms) | 120 | 126 | -5% |
| tap: search osprey blocked (ms) | 242 | 236 | +3% |

By host: sachinwankhede.github.io 145 req / 2210 KB; tiles.openfreemap.org 9 req / 202 KB; server.arcgisonline.com 16 req / 95 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2347 | 2355 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2347 | 2355 | Navigation Timing |
| Load event | 5 | 0 | 3254 | 3275 | Navigation Timing |
| First contentful paint | 5 | 0 | 417 | 471 | Paint Timing |
| App data ready | 5 | 0 | 2350 | 2353 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2350 | 2353 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3249 | 3277 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3724 | 3743 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4584 | 4749 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4667 | 4749 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5830 | 5901 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5850 | 5930 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 15/16; total duration 1738/1789 ms; blocking time over 50 ms 988/1040 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 142. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 153 | 165 |
| DOM interactive | 856 | 872 |
| Load event | 859 | 876 |
| Map loaded | 2013 | 2278 |
| Blocking time before map loaded | 984 | 1128 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 372 | 436 |
| place warm open | 5 | 228 | 279 |
| place first picture arrived | 5 | 515 | 548 |
| place last picture arrived | 5 | 1393 | 1437 |
| food-web cold open | 5 | 1534 | 1564 |
| food-web warm open | 5 | 511 | 605 |
| species selection | 5 | 201 | 208 |

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
| map: map style and index, first request (ms) | 19 | 23 | -16% |
| map: map style and index, last answer (ms) | 57 | 152 | -62% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 663 | 727 | -9% |
| map: map glyphs, last answer (ms) | 686 | 851 | -19% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 303 | 309 | -2% |
| map: satellite tiles, last answer (ms) | 331 | 345 | -4% |
| map: satellite tiles, requests | 4 | 16 | -75% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 85 | 80 | +7% |
| page loaded (ms) | 293 | 290 | +1% |
| map drawn (ms) | 1411 | 1480 | -5% |
| blocked before map (ms) | 581 | 617 | -6% |
| download (KB) | 2260 | 2398 | -6% |
| requests | 55 | 66 | -17% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 130 | 125 | +4% |
| tap: filter on blocked (ms) | 371 | 362 | +2% |
| tap: filter off (ms) | 135 | 131 | +3% |
| tap: filter off blocked (ms) | 459 | 359 | +28% ⚠ |
| tap: state parks on (ms) | 118 | 118 | 0% |
| tap: state parks on blocked (ms) | 569 | 592 | -4% |
| tap: state parks off (ms) | 214 | 214 | 0% |
| tap: state parks off blocked (ms) | 262 | 257 | +2% |
| tap: open place (ms) | 14 | 15 | -7% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 210 | 204 | +3% |
| tap: back from place blocked (ms) | 379 | 325 | +17% ⚠ |
| tap: journeys tab (ms) | 13 | 13 | 0% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 64 | 66 | -3% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 170 | 169 | +1% |
| tap: back from journey blocked (ms) | 355 | 252 | +41% ⚠ |
| tap: search ma (cold) (ms) | 150 | 138 | +9% |
| tap: search ma (cold) blocked (ms) | 473 | 550 | -14% |
| tap: search mar (ms) | 186 | 184 | +1% |
| tap: search mar blocked (ms) | 463 | 499 | -7% |
| tap: search mari (ms) | 187 | 179 | +4% |
| tap: search mari blocked (ms) | 520 | 530 | -2% |
| tap: search osprey (ms) | 173 | 179 | -3% |
| tap: search osprey blocked (ms) | 530 | 538 | -1% |

By host: sachinwankhede.github.io 384 req / 6102 KB; server.arcgisonline.com 60 req / 501 KB; tiles.openfreemap.org 10 req / 242 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 61 | 87 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 61 | 87 | Navigation Timing |
| Load event | 5 | 0 | 293 | 329 | Navigation Timing |
| First contentful paint | 5 | 0 | 85 | 124 | Paint Timing |
| App data ready | 5 | 0 | 154 | 195 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 154 | 195 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 293 | 330 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 327 | 370 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1411 | 1428 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1414 | 1442 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1470 | 1506 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1516 | 1556 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/11; total duration 1081/1147 ms; blocking time over 50 ms 581/607 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 79 | 84 |
| DOM interactive | 166 | 179 |
| Load event | 300 | 319 |
| Map loaded | 1351 | 1427 |
| Blocking time before map loaded | 568 | 606 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 90 | 102 |
| place warm open | 5 | 150 | 164 |
| place first picture arrived | 5 | 43 | 49 |
| place last picture arrived | 5 | 88 | 106 |
| food-web cold open | 5 | 208 | 236 |
| food-web warm open | 5 | 166 | 232 |
| species selection | 5 | 47 | 60 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 38 | 198 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 38 | 198 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 3 | 7 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 3 |
