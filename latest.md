# Site speed, 2026-11-01 19:47 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 428 | 412 | +4% |
| page loaded (ms) | 5358 | 6170 | -13% |
| map drawn (ms) | 6854 | 7653 | -10% |
| blocked before map (ms) | 1691 | 1887 | -10% |
| download (KB) | 1226 | 1206 | +2% |
| requests | 25 | 24 | +4% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 159 | 155 | +3% |
| tap: filter on blocked (ms) | 151 | 154 | -2% |
| tap: filter off (ms) | 149 | 137 | +9% |
| tap: filter off blocked (ms) | 141 | 150 | -6% |
| tap: state parks on (ms) | 577 | 583 | -1% |
| tap: state parks on blocked (ms) | 164 | 175 | -6% |
| tap: state parks off (ms) | 262 | 218 | +20% ⚠ |
| tap: state parks off blocked (ms) | 151 | 127 | +19% ⚠ |
| tap: open place (ms) | 46 | 40 | +15% |
| tap: open place blocked (ms) | 76 | 51 | +49% ⚠ |
| tap: back from place (ms) | 338 | 309 | +9% |
| tap: back from place blocked (ms) | 270 | 251 | +8% |
| tap: journeys tab (ms) | 65 | 52 | +25% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 326 | 330 | -1% |
| tap: open journey blocked (ms) | 8 | 6 | +33% |
| tap: back from journey (ms) | 287 | 291 | -1% |
| tap: back from journey blocked (ms) | 172 | 186 | -8% |

By host: sachinwankhede.github.io 24 req / 1469 KB; server.arcgisonline.com 28 req / 132 KB; fonts.gstatic.com 6 req / 130 KB; thumb.wikimedia.org 12 req / 79 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 4599 | 4725 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 4599 | 4725 | Navigation Timing |
| Load event | 5 | 0 | 5358 | 5463 | Navigation Timing |
| First contentful paint | 5 | 0 | 428 | 586 | Paint Timing |
| App data ready | 5 | 0 | 4594 | 4721 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 4594 | 4721 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 4594 | 4721 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 5172 | 5321 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 6854 | 7017 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 6857 | 7021 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 7315 | 7480 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 7332 | 7500 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 25/26; total duration 2941/3106 ms; blocking time over 50 ms 1691/1856 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 156 | 184 |
| DOM interactive | 1662 | 1760 |
| Load event | 1678 | 1776 |
| Map loaded | 3177 | 3254 |
| Blocking time before map loaded | 1678 | 1715 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 1085 | 1120 |
| place warm open | 5 | 228 | 238 |
| food-web cold open | 5 | 1211 | 1222 |
| food-web warm open | 5 | 273 | 313 |
| species selection | 5 | 209 | 254 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 2 | 145 |
| place warm open | none recorded | 0 | 0 |
| food-web cold open | web data | 2 | 145 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | none recorded | 0 | 0 |

## desktop

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 133 | 184 | -28% |
| page loaded (ms) | 564 | 626 | -10% |
| map drawn (ms) | 1600 | 1640 | -2% |
| blocked before map (ms) | 740 | 739 | +0% |
| download (KB) | 2802 | 2782 | +1% |
| requests | 68 | 67 | +1% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 138 | 136 | +1% |
| tap: filter on blocked (ms) | 379 | 374 | +1% |
| tap: filter off (ms) | 139 | 143 | -3% |
| tap: filter off blocked (ms) | 361 | 360 | +0% |
| tap: state parks on (ms) | 358 | 359 | 0% |
| tap: state parks on blocked (ms) | 308 | 309 | 0% |
| tap: state parks off (ms) | 213 | 218 | -2% |
| tap: state parks off blocked (ms) | 267 | 271 | -1% |
| tap: open place (ms) | 15 | 15 | 0% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 314 | 300 | +5% |
| tap: back from place blocked (ms) | 414 | 392 | +6% |
| tap: journeys tab (ms) | 16 | 15 | +7% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 78 | 78 | 0% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 257 | 252 | +2% |
| tap: back from journey blocked (ms) | 385 | 364 | +6% |

By host: sachinwankhede.github.io 150 req / 3826 KB; thumb.wikimedia.org 46 req / 347 KB; fonts.gstatic.com 14 req / 185 KB; server.arcgisonline.com 40 req / 175 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 563 | 582 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 563 | 582 | Navigation Timing |
| Load event | 5 | 0 | 564 | 583 | Navigation Timing |
| First contentful paint | 5 | 0 | 133 | 186 | Paint Timing |
| App data ready | 5 | 0 | 455 | 469 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 455 | 469 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 455 | 469 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 546 | 611 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1600 | 1730 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1712 | 1730 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1724 | 1824 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1745 | 1849 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 11/11; total duration 1331/1344 ms; blocking time over 50 ms 781/794 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (304, or under 10 KB on the wire): 5; downloaded again (10 KB or more): 0; status 200 x5; body bytes (p50): 143. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 76 | 80 |
| DOM interactive | 489 | 494 |
| Load event | 492 | 497 |
| Map loaded | 1628 | 1698 |
| Blocking time before map loaded | 748 | 756 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 63 | 65 |
| place warm open | 5 | 162 | 178 |
| food-web cold open | 5 | 118 | 128 |
| food-web warm open | 5 | 239 | 280 |
| species selection | 5 | 240 | 252 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 2 | 145 |
| place warm open | none recorded | 0 | 0 |
| food-web cold open | web data | 2 | 145 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | web data | 1 | 184 |
| species selection | photos | 0 | 0 |
