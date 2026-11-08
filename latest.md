# Site speed, 2026-11-08 15:15 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| map: map style and index, first request (ms) | 201 | 189 | +6% |
| map: map style and index, last answer (ms) | 485 | 465 | +4% |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 3632 | 3822 | -5% |
| map: map glyphs, last answer (ms) | 4183 | 4229 | -1% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 3216 | 3312 | -3% |
| map: satellite tiles, last answer (ms) | 3747 | 3770 | -1% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 445 | 429 | +4% |
| page loaded (ms) | 3185 | 3271 | -3% |
| map drawn (ms) | 4578 | 4623 | -1% |
| blocked before map (ms) | 631 | 918 | -31% |
| download (KB) | 790 | 790 | +0% |
| requests | 20 | 20 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 95 | 113 | -16% |
| tap: filter on blocked (ms) | 36 | 127 | -72% |
| tap: filter off (ms) | 92 | 106 | -13% |
| tap: filter off blocked (ms) | 54 | 127 | -57% |
| tap: state parks on (ms) | 97 | 109 | -11% |
| tap: state parks on blocked (ms) | 104 | 215 | -52% |
| tap: state parks off (ms) | 94 | 126 | -25% |
| tap: state parks off blocked (ms) | 27 | 94 | -71% |
| tap: open place (ms) | 23 | 27 | -15% |
| tap: open place blocked (ms) | 33 | 58 | -43% |
| tap: back from place (ms) | 234 | 276 | -15% |
| tap: back from place blocked (ms) | 161 | 248 | -35% |
| tap: journeys tab (ms) | 29 | 37 | -22% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 200 | 256 | -22% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 131 | 167 | -22% |
| tap: back from journey blocked (ms) | 50 | 119 | -58% |
| tap: search ma (cold) (ms) | 82 | 87 | -6% |
| tap: search ma (cold) blocked (ms) | 133 | 265 | -50% |
| tap: search mar (ms) | 125 | 148 | -16% |
| tap: search mar blocked (ms) | 82 | 232 | -65% |
| tap: search mari (ms) | 103 | 123 | -16% |
| tap: search mari blocked (ms) | 64 | 228 | -72% |
| tap: search osprey (ms) | 66 | 80 | -17% |
| tap: search osprey blocked (ms) | 61 | 220 | -72% |

By host: sachinwankhede.github.io 134 req / 1773 KB; server.arcgisonline.com 16 req / 95 KB; tiles.openfreemap.org 7 req / 91 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 2431 | 2446 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 2431 | 2447 | Navigation Timing |
| Load event | 5 | 0 | 3185 | 3243 | Navigation Timing |
| First contentful paint | 5 | 0 | 445 | 579 | Paint Timing |
| App data ready | 5 | 0 | 2434 | 2445 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 2434 | 2445 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 3187 | 3244 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 3597 | 3705 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 4578 | 4601 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 4578 | 4674 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 5730 | 5828 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 5741 | 5851 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 14/16; total duration 1331/1691 ms; blocking time over 50 ms 631/921 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 142. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 128 | 135 |
| DOM interactive | 678 | 696 |
| Load event | 681 | 699 |
| Map loaded | 1615 | 1668 |
| Blocking time before map loaded | 670 | 680 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 328 | 341 |
| place warm open | 5 | 192 | 241 |
| place first picture arrived | 5 | 496 | 499 |
| place last picture arrived | 5 | 1347 | 1371 |
| food-web cold open | 5 | 1357 | 1374 |
| food-web warm open | 5 | 441 | 498 |
| species selection | 5 | 143 | 145 |

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
| map: map style and index, first request (ms) | 46 | 22 | +108% ⚠ |
| map: map style and index, last answer (ms) | 97 | 68 | +44% ⚠ |
| map: map style and index, requests | 1 | 1 | 0% |
| map: vector tiles, first request (ms) | n/a | n/a |  |
| map: vector tiles, last answer (ms) | n/a | n/a |  |
| map: vector tiles, requests | n/a | n/a |  |
| map: map glyphs, first request (ms) | 664 | 732 | -9% |
| map: map glyphs, last answer (ms) | 687 | 761 | -10% |
| map: map glyphs, requests | 1 | 1 | 0% |
| map: satellite tiles, first request (ms) | 281 | 309 | -9% |
| map: satellite tiles, last answer (ms) | 328 | 329 | 0% |
| map: satellite tiles, requests | 4 | 4 | 0% |
| map: terrain tiles, first request (ms) | n/a | n/a |  |
| map: terrain tiles, last answer (ms) | n/a | n/a |  |
| map: terrain tiles, requests | n/a | n/a |  |
| first paint (ms) | 97 | 89 | +9% |
| page loaded (ms) | 273 | 299 | -9% |
| map drawn (ms) | 1240 | 1374 | -10% |
| blocked before map (ms) | 420 | 559 | -25% |
| download (KB) | 2344 | 2344 | +0% |
| requests | 58 | 58 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 107 | 128 | -16% |
| tap: filter on blocked (ms) | 254 | 364 | -30% |
| tap: filter off (ms) | 115 | 138 | -17% |
| tap: filter off blocked (ms) | 309 | 362 | -15% |
| tap: state parks on (ms) | 99 | 119 | -17% |
| tap: state parks on blocked (ms) | 441 | 573 | -23% |
| tap: state parks off (ms) | 181 | 213 | -15% |
| tap: state parks off blocked (ms) | 174 | 252 | -31% |
| tap: open place (ms) | 14 | 15 | -7% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 167 | 204 | -18% |
| tap: back from place blocked (ms) | 262 | 407 | -36% |
| tap: journeys tab (ms) | 13 | 14 | -7% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 52 | 66 | -21% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 140 | 166 | -16% |
| tap: back from journey blocked (ms) | 178 | 326 | -45% |
| tap: search ma (cold) (ms) | 91 | 109 | -17% |
| tap: search ma (cold) blocked (ms) | 397 | 479 | -17% |
| tap: search mar (ms) | 104 | 127 | -18% |
| tap: search mar blocked (ms) | 387 | 489 | -21% |
| tap: search mari (ms) | 106 | 131 | -19% |
| tap: search mari blocked (ms) | 448 | 555 | -19% |
| tap: search osprey (ms) | 106 | 135 | -21% |
| tap: search osprey blocked (ms) | 468 | 592 | -21% |

By host: sachinwankhede.github.io 351 req / 4716 KB; server.arcgisonline.com 66 req / 509 KB; tiles.openfreemap.org 8 req / 131 KB;  12 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 74 | 83 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 74 | 83 | Navigation Timing |
| Load event | 5 | 0 | 273 | 285 | Navigation Timing |
| First contentful paint | 5 | 0 | 97 | 108 | Paint Timing |
| App data ready | 5 | 0 | 151 | 173 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 151 | 173 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 272 | 286 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 323 | 404 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1240 | 1376 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1240 | 1376 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1309 | 1432 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1345 | 1458 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 9/10; total duration 872/907 ms; blocking time over 50 ms 420/433 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 142. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 64 | 77 |
| DOM interactive | 70 | 148 |
| Load event | 248 | 256 |
| Map loaded | 1171 | 1199 |
| Blocking time before map loaded | 389 | 414 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 52 | 53 |
| place warm open | 5 | 58 | 112 |
| place first picture arrived | 5 | 56 | 59 |
| place last picture arrived | 5 | 76 | 83 |
| food-web cold open | 5 | 158 | 162 |
| food-web warm open | 5 | 133 | 192 |
| species selection | 5 | 48 | 56 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 7 |
| place cold open | photos | 0 | 0 |
| place warm open | none recorded | 0 | 0 |
| place first picture arrived | none recorded | 0 | 0 |
| place last picture arrived | pictures | 36 | 163 |
| food-web cold open | web data | 1 | 7 |
| food-web cold open | other | 1 | 94 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | other | 2 | 4 |
