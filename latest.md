# Site speed, 2026-11-07 14:55 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 189 | 183 | +3% |
| map: map style and index, last answer (ms) | 465 | 418 | +11% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3822 | 3492 | +9% |
| map: map glyphs, last answer (ms) | 4229 | 4101 | +3% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3312 | 3180 | +4% |
| map: satellite tiles, last answer (ms) | 3770 | 3673 | +3% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 429 | 415 | +3% |
| page loaded (ms) | 3271 | 3152 | +4% |
| map drawn (ms) | 4623 | 4386 | +5% |
| blocked before map (ms) | 918 | 486 | +89% ⚠ |
| download (KB) | 790 | 790 | 0% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 113 | 78 | +45% ⚠ |
| tap: filter on blocked (ms) | 127 | 0 |  |
| tap: filter off (ms) | 106 | 72 | +47% ⚠ |
| tap: filter off blocked (ms) | 127 | 0 |  |
| tap: state parks on (ms) | 109 | 77 | +42% ⚠ |
| tap: state parks on blocked (ms) | 215 | 4 | +5275% ⚠ |
| tap: state parks off (ms) | 126 | 83 | +52% ⚠ |
| tap: state parks off blocked (ms) | 94 | 0 |  |
| tap: open place (ms) | 27 | 25 | +8% |
| tap: open place blocked (ms) | 58 | 20 | +190% ⚠ |
| tap: back from place (ms) | 276 | 188 | +47% ⚠ |
| tap: back from place blocked (ms) | 248 | 92 | +170% ⚠ |
| tap: journeys tab (ms) | 37 | 26 | +42% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 256 | 180 | +42% ⚠ |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 167 | 111 | +50% ⚠ |
| tap: back from journey blocked (ms) | 119 | 18 | +561% ⚠ |
| tap: search ma (cold) (ms) | 87 | 73 | +19% |
| tap: search ma (cold) blocked (ms) | 265 | 50 | +430% ⚠ |
| tap: search mar (ms) | 148 | 119 | +24% ⚠ |
| tap: search mar blocked (ms) | 232 | 5 | +4540% ⚠ |
| tap: search mari (ms) | 123 | 90 | +37% ⚠ |
| tap: search mari blocked (ms) | 228 | 0 |  |
| tap: search osprey (ms) | 80 | 55 | +45% ⚠ |
| tap: search osprey blocked (ms) | 220 | 0 |  |

By host: sachinwankhede.github.io 135 req / 1775 KB; server.arcgisonline.com 16 req / 95 KB; tiles.openfreemap.org 7 req / 91 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2444 | 2525 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2444 | 2525 | Navigation Timing |
| Load event | 5 | 0 | 3271 | 3363 | Navigation Timing |
| First contentful paint | 5 | 0 | 429 | 595 | Paint Timing |
| App data ready | 5 | 0 | 2442 | 2528 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2442 | 2528 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3271 | 3363 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3770 | 3844 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4623 | 4640 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4644 | 4664 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5783 | 5934 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5809 | 5956 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 14/14; total duration 1634/1669 ms; blocking time over 50 ms 934/969 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 149 | 155 |
| DOM interactive | 810 | 842 |
| Load event | 813 | 845 |
| Map loaded | 1962 | 2051 |
| Blocking time before map loaded | 932 | 1018 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 366 | 475 |
| place warm open | 5 | 199 | 245 |
| place first picture arrived | 5 | 498 | 601 |
| place last picture arrived | 5 | 1393 | 1493 |
| food-web cold open | 5 | 1428 | 1609 |
| food-web warm open | 5 | 512 | 614 |
| species selection | 5 | 177 | 189 |

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
| map: map style and index, first request (ms) | 22 | 20 | +10% |
| map: map style and index, last answer (ms) | 68 | 50 | +35% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 732 | 608 | +20% ⚠ |
| map: map glyphs, last answer (ms) | 761 | 640 | +19% ⚠ |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 309 | 242 | +28% ⚠ |
| map: satellite tiles, last answer (ms) | 329 | 259 | +27% ⚠ |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 89 | 67 | +32% ⚠ |
| page loaded (ms) | 299 | 228 | +31% ⚠ |
| map drawn (ms) | 1374 | 999 | +38% ⚠ |
| blocked before map (ms) | 559 | 263 | +113% ⚠ |
| download (KB) | 2344 | 2344 | +0% |
| requests | 58 | 58 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 128 | 87 | +47% ⚠ |
| tap: filter on blocked (ms) | 364 | 123 | +196% ⚠ |
| tap: filter off (ms) | 138 | 96 | +44% ⚠ |
| tap: filter off blocked (ms) | 362 | 146 | +148% ⚠ |
| tap: state parks on (ms) | 119 | 81 | +47% ⚠ |
| tap: state parks on blocked (ms) | 573 | 295 | +94% ⚠ |
| tap: state parks off (ms) | 213 | 139 | +53% ⚠ |
| tap: state parks off blocked (ms) | 252 | 80 | +215% ⚠ |
| tap: open place (ms) | 15 | 12 | +25% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 204 | 147 | +39% ⚠ |
| tap: back from place blocked (ms) | 407 | 124 | +228% ⚠ |
| tap: journeys tab (ms) | 14 | 12 | +17% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 66 | 53 | +25% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 166 | 117 | +42% ⚠ |
| tap: back from journey blocked (ms) | 326 | 107 | +205% ⚠ |
| tap: search ma (cold) (ms) | 109 | 71 | +54% ⚠ |
| tap: search ma (cold) blocked (ms) | 479 | 243 | +97% ⚠ |
| tap: search mar (ms) | 127 | 89 | +43% ⚠ |
| tap: search mar blocked (ms) | 489 | 219 | +123% ⚠ |
| tap: search mari (ms) | 131 | 78 | +68% ⚠ |
| tap: search mari blocked (ms) | 555 | 289 | +92% ⚠ |
| tap: search osprey (ms) | 135 | 87 | +55% ⚠ |
| tap: search osprey blocked (ms) | 592 | 323 | +83% ⚠ |

By host: sachinwankhede.github.io 354 req / 4750 KB; server.arcgisonline.com 61 req / 508 KB; tiles.openfreemap.org 8 req / 131 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 63 | 77 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 63 | 77 | Navigation Timing |
| Load event | 5 | 0 | 299 | 321 | Navigation Timing |
| First contentful paint | 5 | 0 | 89 | 101 | Paint Timing |
| App data ready | 5 | 0 | 153 | 187 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 153 | 187 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 298 | 322 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 328 | 476 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1374 | 1391 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1374 | 1511 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1438 | 1569 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1469 | 1598 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 11/11; total duration 1107/1160 ms; blocking time over 50 ms 575/610 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 153. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 80 | 90 |
| DOM interactive | 177 | 179 |
| Load event | 313 | 321 |
| Map loaded | 1417 | 1436 |
| Blocking time before map loaded | 594 | 613 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 70 | 74 |
| place warm open | 5 | 55 | 57 |
| place first picture arrived | 5 | 56 | 67 |
| place last picture arrived | 5 | 121 | 185 |
| food-web cold open | 5 | 202 | 237 |
| food-web warm open | 5 | 169 | 236 |
| species selection | 5 | 52 | 59 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 3 | 8 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 38 | 198 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web cold open | photos | 1 | 3 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 0 | 0 |
