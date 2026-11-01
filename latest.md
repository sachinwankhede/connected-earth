# Site speed, 2026-11-01 16:46 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 412 | 423 | -3% |
| page loaded (ms) | 6170 | 6023 | +2% |
| map drawn (ms) | 7653 | 7388 | +4% |
| blocked before map (ms) | 1887 | 1273 | +48% ⚠ |
| download (KB) | 1206 | 1206 | +0% |
| requests | 24 | 24 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 155 | 133 | +17% ⚠ |
| tap: filter on blocked (ms) | 154 | 72 | +114% ⚠ |
| tap: filter off (ms) | 137 | 129 | +6% |
| tap: filter off blocked (ms) | 150 | 53 | +183% ⚠ |
| tap: state parks on (ms) | 583 | 411 | +42% ⚠ |
| tap: state parks on blocked (ms) | 175 | 95 | +84% ⚠ |
| tap: state parks off (ms) | 218 | 167 | +31% ⚠ |
| tap: state parks off blocked (ms) | 127 | 63 | +102% ⚠ |
| tap: open place (ms) | 40 | 33 | +21% |
| tap: open place blocked (ms) | 51 | 26 | +96% ⚠ |
| tap: back from place (ms) | 309 | 264 | +17% ⚠ |
| tap: back from place blocked (ms) | 251 | 145 | +73% ⚠ |
| tap: journeys tab (ms) | 52 | 40 | +30% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 330 | 233 | +42% ⚠ |
| tap: open journey blocked (ms) | 6 | 0 |  |
| tap: back from journey (ms) | 291 | 241 | +21% ⚠ |
| tap: back from journey blocked (ms) | 186 | 111 | +68% ⚠ |

By host: sachinwankhede.github.io 22 req / 1449 KB; server.arcgisonline.com 28 req / 132 KB; fonts.gstatic.com 6 req / 130 KB; thumb.wikimedia.org 12 req / 79 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 5427 | 5463 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 5427 | 5463 | Navigation Timing |
| Load event | 5 | 0 | 6170 | 6246 | Navigation Timing |
| First contentful paint | 5 | 0 | 412 | 484 | Paint Timing |
| App data ready | 5 | 0 | 5435 | 5458 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 5435 | 5460 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 5435 | 5460 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 6019 | 6035 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 7653 | 7700 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 7699 | 7717 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 8148 | 8164 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 8174 | 8196 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 25/25; total duration 3137/3174 ms; blocking time over 50 ms 1895/1928 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (empty body or 304): 0; downloaded again (body bytes on the wire): 5; status 200 x5; body bytes (p50): 144. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 159 | 245 |
| DOM interactive | 1917 | 2036 |
| Load event | 1930 | 2050 |
| Map loaded | 3303 | 3400 |
| Blocking time before map loaded | 1810 | 1893 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 349 | 355 |
| place warm open | 5 | 223 | 279 |
| food-web cold open | 5 | 486 | 492 |
| food-web warm open | 5 | 272 | 323 |
| species selection | 5 | 171 | 234 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 5 |
| place warm open | none recorded | 0 | 0 |
| food-web cold open | web data | 1 | 5 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | none recorded | 0 | 0 |

## desktop

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 184 | 125 | +47% ⚠ |
| page loaded (ms) | 626 | 508 | +23% ⚠ |
| map drawn (ms) | 1640 | 1445 | +13% |
| blocked before map (ms) | 739 | 571 | +29% ⚠ |
| download (KB) | 2782 | 2782 | +0% |
| requests | 67 | 67 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 136 | 111 | +23% ⚠ |
| tap: filter on blocked (ms) | 374 | 251 | +49% ⚠ |
| tap: filter off (ms) | 143 | 117 | +22% ⚠ |
| tap: filter off blocked (ms) | 360 | 245 | +47% ⚠ |
| tap: state parks on (ms) | 359 | 277 | +30% ⚠ |
| tap: state parks on blocked (ms) | 309 | 214 | +44% ⚠ |
| tap: state parks off (ms) | 218 | 177 | +23% ⚠ |
| tap: state parks off blocked (ms) | 271 | 176 | +54% ⚠ |
| tap: open place (ms) | 15 | 14 | +7% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 300 | 243 | +23% ⚠ |
| tap: back from place blocked (ms) | 392 | 288 | +36% ⚠ |
| tap: journeys tab (ms) | 15 | 12 | +25% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 78 | 62 | +26% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 252 | 205 | +23% ⚠ |
| tap: back from journey blocked (ms) | 364 | 296 | +23% ⚠ |

By host: sachinwankhede.github.io 148 req / 3807 KB; thumb.wikimedia.org 46 req / 348 KB; fonts.gstatic.com 14 req / 185 KB; server.arcgisonline.com 40 req / 175 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 625 | 709 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 625 | 709 | Navigation Timing |
| Load event | 5 | 0 | 626 | 712 | Navigation Timing |
| First contentful paint | 5 | 0 | 184 | 248 | Paint Timing |
| App data ready | 5 | 0 | 512 | 667 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 512 | 667 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 512 | 667 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 572 | 743 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1640 | 1812 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1672 | 1839 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1690 | 1929 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1717 | 1950 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/11; total duration 1302/1361 ms; blocking time over 50 ms 802/821 ms.

### Returning visit, service worker on (observational)

A first visit installs the service worker and fills its caches; a second page in the same browser context is then timed. Throttling is attached to the page, so requests made by the service worker itself may not be slowed: read the document line below to see whether the page was downloaded again or only re-checked. Not compared with history and never raises a warning.

Samples: 5; service worker ready: 5; page controlled by the worker on the second visit: 5. Page document: status 200 x5; answered by the worker: 5. The worker's own network fetch of the document: re-checked only (empty body or 304): 0; downloaded again (body bytes on the wire): 5; status 200 x5; body bytes (p50): 153. Seen only when the run sets PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1.

| Metric | p50 (ms) | p95 (ms) |
|---|---:|---:|
| First contentful paint | 77 | 263 |
| DOM interactive | 542 | 720 |
| Load event | 546 | 723 |
| Map loaded | 1691 | 1943 |
| Blocking time before map loaded | 785 | 863 |

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 51 | 179 |
| place warm open | 5 | 71 | 161 |
| food-web cold open | 5 | 94 | 104 |
| food-web warm open | 5 | 221 | 227 |
| species selection | 5 | 278 | 310 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 5 |
| place warm open | photos | 0 | 0 |
| food-web cold open | web data | 1 | 5 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | web data | 1 | 184 |
| species selection | photos | 34 | 209 |
