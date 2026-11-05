# Site speed, 2026-11-05 16:30 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 203 | 174 | +17% ⚠ |
| map: map style and index, last answer (ms) | 411 | 424 | -3% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3900 | 3795 | +3% |
| map: map glyphs, last answer (ms) | 4280 | 4280 | +0% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3334 | 3294 | +1% |
| map: satellite tiles, last answer (ms) | 3746 | 3830 | -2% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 445 | 417 | +7% |
| page loaded (ms) | 3292 | 3254 | +1% |
| map drawn (ms) | 4822 | 4584 | +5% |
| blocked before map (ms) | 1109 | 988 | +12% |
| download (KB) | 789 | 782 | +1% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 126 | 126 | 0% |
| tap: filter on blocked (ms) | 249 | 107 | +133% ⚠ |
| tap: filter off (ms) | 121 | 112 | +8% |
| tap: filter off blocked (ms) | 261 | 147 | +78% ⚠ |
| tap: state parks on (ms) | 131 | 120 | +9% |
| tap: state parks on blocked (ms) | 349 | 217 | +61% ⚠ |
| tap: state parks off (ms) | 139 | 125 | +11% |
| tap: state parks off blocked (ms) | 172 | 109 | +58% ⚠ |
| tap: open place (ms) | 29 | 27 | +7% |
| tap: open place blocked (ms) | 55 | 58 | -5% |
| tap: back from place (ms) | 324 | 287 | +13% |
| tap: back from place blocked (ms) | 368 | 261 | +41% ⚠ |
| tap: journeys tab (ms) | 39 | 39 | 0% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 272 | 261 | +4% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 191 | 164 | +16% ⚠ |
| tap: back from journey blocked (ms) | 227 | 121 | +88% ⚠ |
| tap: search ma (cold) (ms) | 108 | 173 | -38% |
| tap: search ma (cold) blocked (ms) | 368 | 230 | +60% ⚠ |
| tap: search mar (ms) | 102 | 149 | -32% |
| tap: search mar blocked (ms) | 360 | 236 | +53% ⚠ |
| tap: search mari (ms) | 171 | 171 | 0% |
| tap: search mari blocked (ms) | 370 | 234 | +58% ⚠ |
| tap: search osprey (ms) | 98 | 120 | -18% |
| tap: search osprey blocked (ms) | 370 | 242 | +53% ⚠ |

By host: sachinwankhede.github.io 141 req / 2079 KB; tiles.openfreemap.org 8 req / 145 KB; server.arcgisonline.com 16 req / 95 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2468 | 2516 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2468 | 2516 | Navigation Timing |
| Load event | 5 | 0 | 3292 | 3329 | Navigation Timing |
| First contentful paint | 5 | 0 | 445 | 529 | Paint Timing |
| App data ready | 5 | 0 | 2465 | 2518 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2465 | 2519 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3293 | 3325 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3656 | 3811 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4822 | 4826 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4822 | 4826 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5951 | 5959 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5977 | 5981 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 14/14; total duration 1809/1819 ms; blocking time over 50 ms 1109/1119 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 144. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 162 | 171 |
| DOM interactive | 840 | 849 |
| Load event | 844 | 853 |
| Map loaded | 2156 | 2203 |
| Blocking time before map loaded | 1035 | 1078 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 375 | 387 |
| place warm open | 5 | 214 | 235 |
| place first picture arrived | 5 | 520 | 532 |
| place last picture arrived | 5 | 1389 | 1403 |
| food-web cold open | 5 | 1537 | 1569 |
| food-web warm open | 5 | 587 | 595 |
| species selection | 5 | 194 | 205 |

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
| map: map style and index, first request (ms) | 59 | 19 | +204% ⚠ |
| map: map style and index, last answer (ms) | 83 | 57 | +45% ⚠ |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 741 | 663 | +12% |
| map: map glyphs, last answer (ms) | 757 | 686 | +10% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 345 | 303 | +14% |
| map: satellite tiles, last answer (ms) | 362 | 331 | +9% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 127 | 85 | +49% ⚠ |
| page loaded (ms) | 334 | 293 | +14% |
| map drawn (ms) | 1531 | 1411 | +9% |
| blocked before map (ms) | 694 | 581 | +19% ⚠ |
| download (KB) | 2267 | 2260 | +0% |
| requests | 55 | 55 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 162 | 130 | +25% ⚠ |
| tap: filter on blocked (ms) | 431 | 371 | +16% ⚠ |
| tap: filter off (ms) | 167 | 135 | +24% ⚠ |
| tap: filter off blocked (ms) | 498 | 459 | +8% |
| tap: state parks on (ms) | 151 | 118 | +28% ⚠ |
| tap: state parks on blocked (ms) | 690 | 569 | +21% ⚠ |
| tap: state parks off (ms) | 248 | 214 | +16% ⚠ |
| tap: state parks off blocked (ms) | 332 | 262 | +27% ⚠ |
| tap: open place (ms) | 13 | 14 | -7% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 261 | 210 | +24% ⚠ |
| tap: back from place blocked (ms) | 559 | 379 | +47% ⚠ |
| tap: journeys tab (ms) | 15 | 13 | +15% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 70 | 64 | +9% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 203 | 170 | +19% ⚠ |
| tap: back from journey blocked (ms) | 382 | 355 | +8% |
| tap: search ma (cold) (ms) | 140 | 150 | -7% |
| tap: search ma (cold) blocked (ms) | 633 | 473 | +34% ⚠ |
| tap: search mar (ms) | 178 | 186 | -4% |
| tap: search mar blocked (ms) | 655 | 463 | +41% ⚠ |
| tap: search mari (ms) | 170 | 187 | -9% |
| tap: search mari blocked (ms) | 653 | 520 | +26% ⚠ |
| tap: search osprey (ms) | 135 | 173 | -22% |
| tap: search osprey blocked (ms) | 651 | 530 | +23% ⚠ |

By host: sachinwankhede.github.io 387 req / 6118 KB; tiles.openfreemap.org 9 req / 186 KB; server.arcgisonline.com 28 req / 180 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 101 | 107 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 101 | 107 | Navigation Timing |
| Load event | 5 | 0 | 334 | 340 | Navigation Timing |
| First contentful paint | 5 | 0 | 127 | 135 | Paint Timing |
| App data ready | 5 | 0 | 200 | 208 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 200 | 208 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 335 | 341 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 361 | 463 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1531 | 1600 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1531 | 1600 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1606 | 1658 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1649 | 1706 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/10; total duration 1194/1221 ms; blocking time over 50 ms 694/721 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 144. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 83 | 90 |
| DOM interactive | 97 | 159 |
| Load event | 305 | 316 |
| Map loaded | 1510 | 1583 |
| Blocking time before map loaded | 693 | 748 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 68 | 73 |
| place warm open | 5 | 62 | 73 |
| place first picture arrived | 5 | 75 | 90 |
| place last picture arrived | 5 | 118 | 191 |
| food-web cold open | 5 | 234 | 240 |
| food-web warm open | 5 | 168 | 234 |
| species selection | 5 | 55 | 59 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 38 | 198 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 4 |
