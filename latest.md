# Site speed, 2026-11-03 16:17 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 176 | 182 | -4% |
| map: map style and index, last answer (ms) | 492 | 396 | +24% ⚠ |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 4031 | 4032 | 0% |
| map: map glyphs, last answer (ms) | 4874 | 5068 | -4% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3526 | 3617 | -3% |
| map: satellite tiles, last answer (ms) | 4573 | 4797 | -5% |
| map: satellite tiles, requests | 12 | 12 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 415 | 397 | +5% |
| page loaded (ms) | 3451 | 3576 | -4% |
| map drawn (ms) | 5322 | 5451 | -2% |
| blocked before map (ms) | 1015 | 719 | +41% ⚠ |
| download (KB) | 877 | 1078 | -19% |
| requests | 27 | 26 | +4% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 106 | 97 | +9% |
| tap: filter on blocked (ms) | 115 | 18 | +539% ⚠ |
| tap: filter off (ms) | 104 | 96 | +8% |
| tap: filter off blocked (ms) | 134 | 21 | +538% ⚠ |
| tap: state parks on (ms) | 115 | 114 | +1% |
| tap: state parks on blocked (ms) | 246 | 33 | +645% ⚠ |
| tap: state parks off (ms) | 121 | 90 | +34% ⚠ |
| tap: state parks off blocked (ms) | 90 | 15 | +500% ⚠ |
| tap: open place (ms) | 29 | 29 | 0% |
| tap: open place blocked (ms) | 56 | 39 | +44% |
| tap: back from place (ms) | 268 | 235 | +14% |
| tap: back from place blocked (ms) | 256 | 123 | +108% ⚠ |
| tap: journeys tab (ms) | 37 | 29 | +28% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 266 | 236 | +13% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 165 | 148 | +11% |
| tap: back from journey blocked (ms) | 126 | 44 | +186% ⚠ |
| tap: search ma (cold) (ms) | 172 | n/a |  |
| tap: search ma (cold) blocked (ms) | 246 | n/a |  |
| tap: search mar (ms) | 158 | n/a |  |
| tap: search mar blocked (ms) | 227 | n/a |  |
| tap: search mari (ms) | 176 | n/a |  |
| tap: search mari blocked (ms) | 249 | n/a |  |
| tap: search osprey (ms) | 126 | n/a |  |
| tap: search osprey blocked (ms) | 236 | n/a |  |

By host: sachinwankhede.github.io 142 req / 2223 KB; tiles.openfreemap.org 9 req / 202 KB; server.arcgisonline.com 44 req / 175 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2517 | 2554 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2517 | 2554 | Navigation Timing |
| Load event | 5 | 0 | 3451 | 3477 | Navigation Timing |
| First contentful paint | 5 | 0 | 415 | 475 | Paint Timing |
| App data ready | 5 | 0 | 2514 | 2552 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2515 | 2552 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3452 | 3461 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3989 | 4065 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 5322 | 5338 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 5322 | 5338 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5776 | 5787 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5791 | 5799 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 21/21; total duration 2026/2099 ms; blocking time over 50 ms 1015/1049 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 142. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 146 | 153 |
| DOM interactive | 825 | 836 |
| Load event | 827 | 839 |
| Map loaded | 2107 | 2230 |
| Blocking time before map loaded | 976 | 1034 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 368 | 376 |
| place warm open | 5 | 217 | 264 |
| place first picture arrived | 5 | 502 | 518 |
| place last picture arrived | 5 | 1392 | 1401 |
| food-web cold open | 5 | 1445 | 1455 |
| food-web warm open | 5 | 519 | 581 |
| species selection | 5 | 188 | 191 |

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
| map: map style and index, first request (ms) | 23 | 25 | -8% |
| map: map style and index, last answer (ms) | 152 | 74 | +106% ⚠ |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 727 | 537 | +35% ⚠ |
| map: map glyphs, last answer (ms) | 851 | 563 | +51% ⚠ |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 309 | 268 | +15% ⚠ |
| map: satellite tiles, last answer (ms) | 345 | 302 | +14% |
| map: satellite tiles, requests | 16 | 16 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 80 | 155 | -48% |
| page loaded (ms) | 290 | 255 | +14% |
| map drawn (ms) | 1480 | 1183 | +25% ⚠ |
| blocked before map (ms) | 617 | 395 | +56% ⚠ |
| download (KB) | 2398 | 2599 | -8% |
| requests | 66 | 65 | +2% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 125 | 102 | +23% ⚠ |
| tap: filter on blocked (ms) | 362 | 219 | +65% ⚠ |
| tap: filter off (ms) | 131 | 110 | +19% ⚠ |
| tap: filter off blocked (ms) | 359 | 258 | +39% ⚠ |
| tap: state parks on (ms) | 118 | 252 | -53% |
| tap: state parks on blocked (ms) | 592 | 186 | +218% ⚠ |
| tap: state parks off (ms) | 214 | 176 | +22% ⚠ |
| tap: state parks off blocked (ms) | 257 | 155 | +66% ⚠ |
| tap: open place (ms) | 15 | 12 | +25% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 204 | 230 | -11% |
| tap: back from place blocked (ms) | 325 | 279 | +16% ⚠ |
| tap: journeys tab (ms) | 13 | 24 | -46% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 66 | 57 | +16% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 169 | 135 | +25% ⚠ |
| tap: back from journey blocked (ms) | 252 | 188 | +34% ⚠ |
| tap: search ma (cold) (ms) | 138 | n/a |  |
| tap: search ma (cold) blocked (ms) | 550 | n/a |  |
| tap: search mar (ms) | 184 | n/a |  |
| tap: search mar blocked (ms) | 499 | n/a |  |
| tap: search mari (ms) | 179 | n/a |  |
| tap: search mari blocked (ms) | 530 | n/a |  |
| tap: search osprey (ms) | 179 | n/a |  |
| tap: search osprey blocked (ms) | 538 | n/a |  |

By host: sachinwankhede.github.io 381 req / 6115 KB; server.arcgisonline.com 80 req / 458 KB; tiles.openfreemap.org 10 req / 242 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 57 | 61 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 57 | 61 | Navigation Timing |
| Load event | 5 | 0 | 290 | 301 | Navigation Timing |
| First contentful paint | 5 | 0 | 80 | 86 | Paint Timing |
| App data ready | 5 | 0 | 154 | 157 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 154 | 157 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 291 | 301 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 334 | 412 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1480 | 1492 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1480 | 1492 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1491 | 1506 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1521 | 1550 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 11/12; total duration 1162/1226 ms; blocking time over 50 ms 617/651 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 76 | 85 |
| DOM interactive | 167 | 175 |
| Load event | 312 | 319 |
| Map loaded | 1428 | 1508 |
| Blocking time before map loaded | 608 | 654 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 76 | 81 |
| place warm open | 5 | 61 | 131 |
| place first picture arrived | 5 | 46 | 55 |
| place last picture arrived | 5 | 83 | 100 |
| food-web cold open | 5 | 204 | 221 |
| food-web warm open | 5 | 235 | 261 |
| species selection | 5 | 51 | 65 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 30 | 57 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 38 | 198 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 4 | 9 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 3 |
