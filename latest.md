# Site speed, 2026-11-01 15:13 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 423 | 468 | -10% |
| page loaded (ms) | 6023 | 5893 | +2% |
| map drawn (ms) | 7388 | 7632 | -3% |
| blocked before map (ms) | 1273 | 1688 | -25% |
| download (KB) | 1206 | 1205 | +0% |
| requests | 24 | 24 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 133 | 148 | -10% |
| tap: filter on blocked (ms) | 72 | 151 | -52% |
| tap: filter off (ms) | 129 | 145 | -11% |
| tap: filter off blocked (ms) | 53 | 146 | -64% |
| tap: state parks on (ms) | 411 | 445 | -8% |
| tap: state parks on blocked (ms) | 95 | 155 | -39% |
| tap: state parks off (ms) | 167 | 192 | -13% |
| tap: state parks off blocked (ms) | 63 | 131 | -52% |
| tap: open place (ms) | 33 | 41 | -20% |
| tap: open place blocked (ms) | 26 | 39 | -33% |
| tap: back from place (ms) | 264 | 294 | -10% |
| tap: back from place blocked (ms) | 145 | 260 | -44% |
| tap: journeys tab (ms) | 40 | 48 | -17% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 233 | 286 | -19% |
| tap: open journey blocked (ms) | 0 | 6 | -100% |
| tap: back from journey (ms) | 241 | 282 | -15% |
| tap: back from journey blocked (ms) | 111 | 183 | -39% |

By host: sachinwankhede.github.io 22 req / 1449 KB; server.arcgisonline.com 28 req / 132 KB; fonts.gstatic.com 6 req / 130 KB; thumb.wikimedia.org 12 req / 79 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 5166 | 5529 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 5167 | 5529 | Navigation Timing |
| Load event | 5 | 0 | 6023 | 6142 | Navigation Timing |
| First contentful paint | 5 | 0 | 423 | 737 | Paint Timing |
| App data ready | 5 | 0 | 5161 | 5524 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 5161 | 5524 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 5161 | 5524 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 5692 | 6123 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 7388 | 7753 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 7388 | 7753 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 7841 | 8219 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 7862 | 8236 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 14/15; total duration 1976/2094 ms; blocking time over 50 ms 1273/1346 ms.

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 313 | 326 |
| place warm open | 5 | 176 | 221 |
| food-web cold open | 5 | 416 | 419 |
| food-web warm open | 5 | 204 | 217 |
| species selection | 5 | 163 | 203 |

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
| first paint (ms) | 125 | 247 | -49% |
| page loaded (ms) | 508 | 663 | -23% |
| map drawn (ms) | 1445 | 1809 | -20% |
| blocked before map (ms) | 571 | 802 | -29% |
| download (KB) | 2782 | 2781 | +0% |
| requests | 67 | 67 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 111 | 137 | -19% |
| tap: filter on blocked (ms) | 251 | 412 | -39% |
| tap: filter off (ms) | 117 | 146 | -20% |
| tap: filter off blocked (ms) | 245 | 401 | -39% |
| tap: state parks on (ms) | 277 | 327 | -15% |
| tap: state parks on blocked (ms) | 214 | 334 | -36% |
| tap: state parks off (ms) | 177 | 224 | -21% |
| tap: state parks off blocked (ms) | 176 | 316 | -44% |
| tap: open place (ms) | 14 | 15 | -7% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 243 | 297 | -18% |
| tap: back from place blocked (ms) | 288 | 472 | -39% |
| tap: journeys tab (ms) | 12 | 16 | -25% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 62 | 79 | -22% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 205 | 260 | -21% |
| tap: back from journey blocked (ms) | 296 | 410 | -28% |

By host: sachinwankhede.github.io 148 req / 3807 KB; thumb.wikimedia.org 46 req / 348 KB; fonts.gstatic.com 14 req / 185 KB; server.arcgisonline.com 40 req / 175 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 507 | 516 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 507 | 516 | Navigation Timing |
| Load event | 5 | 0 | 508 | 517 | Navigation Timing |
| First contentful paint | 5 | 0 | 125 | 165 | Paint Timing |
| App data ready | 5 | 0 | 419 | 431 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 419 | 431 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 419 | 431 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 465 | 484 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1445 | 1482 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1445 | 1482 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1469 | 1496 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1482 | 1522 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 10/11; total duration 1071/1122 ms; blocking time over 50 ms 571/582 ms.

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 42 | 43 |
| place warm open | 5 | 56 | 132 |
| food-web cold open | 5 | 72 | 79 |
| food-web warm open | 5 | 176 | 178 |
| species selection | 5 | 176 | 192 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 5 |
| place warm open | none recorded | 0 | 0 |
| food-web cold open | web data | 1 | 5 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | web data | 1 | 184 |
