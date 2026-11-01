# Site speed, 2026-11-01 03:06 UTC

https://sachinwankhede.github.io/connected-earth/  
Median of 5 runs per profile. Phone: 4x slower CPU, 1.6 Mbps, 150 ms latency. Desktop: no throttling. Results depend on the runner and network used for this URL. A mark ⚠ means more than 15% worse than the previous run.

## phone

| Metric | Now | Previous | Change |
|---|---|---|---|
| first paint (ms) | 468 | 425 | +10% |
| page loaded (ms) | 5893 | 5483 | +7% |
| map drawn (ms) | 7632 | 7273 | +5% |
| blocked before map (ms) | 1688 | 1740 | -3% |
| download (KB) | 1205 | 1143 | +5% |
| requests | 24 | 24 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 148 | 142 | +4% |
| tap: filter on blocked (ms) | 151 | 131 | +15% |
| tap: filter off (ms) | 145 | 133 | +9% |
| tap: filter off blocked (ms) | 146 | 134 | +9% |
| tap: state parks on (ms) | 445 | 482 | -8% |
| tap: state parks on blocked (ms) | 155 | 112 | +38% ⚠ |
| tap: state parks off (ms) | 192 | 179 | +7% |
| tap: state parks off blocked (ms) | 131 | 97 | +35% ⚠ |
| tap: open place (ms) | 41 | 39 | +5% |
| tap: open place blocked (ms) | 39 | 51 | -24% |
| tap: back from place (ms) | 294 | 302 | -3% |
| tap: back from place blocked (ms) | 260 | 228 | +14% |
| tap: journeys tab (ms) | 48 | 43 | +12% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 286 | 285 | +0% |
| tap: open journey blocked (ms) | 6 | 2 | +200% |
| tap: back from journey (ms) | 282 | 274 | +3% |
| tap: back from journey blocked (ms) | 183 | 184 | -1% |

By host: sachinwankhede.github.io 21 req / 1447 KB; server.arcgisonline.com 28 req / 132 KB; fonts.gstatic.com 6 req / 130 KB; thumb.wikimedia.org 12 req / 79 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 5305 | 5438 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 5305 | 5438 | Navigation Timing |
| Load event | 5 | 0 | 5893 | 6132 | Navigation Timing |
| First contentful paint | 5 | 0 | 468 | 585 | Paint Timing |
| App data ready | 5 | 0 | 5300 | 5568 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 5301 | 5568 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 5301 | 5568 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 5877 | 6038 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 7632 | 7684 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 7631 | 7684 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 8088 | 8138 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 8109 | 8162 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 25/26; total duration 2981/3023 ms; blocking time over 50 ms 1688/1763 ms.

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 340 | 343 |
| place warm open | 5 | 213 | 220 |
| food-web cold open | 5 | 465 | 469 |
| food-web warm open | 5 | 345 | 359 |
| species selection | 5 | 180 | 184 |

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
| first paint (ms) | 247 | 179 | +38% ⚠ |
| page loaded (ms) | 663 | 598 | +11% |
| map drawn (ms) | 1809 | 1706 | +6% |
| blocked before map (ms) | 802 | 790 | +2% |
| download (KB) | 2781 | 2719 | +2% |
| requests | 67 | 67 | 0% |
| Wikipedia requests | 0 | 0 |  |
| tap: filter on (ms) | 137 | 129 | +6% |
| tap: filter on blocked (ms) | 412 | 368 | +12% |
| tap: filter off (ms) | 146 | 140 | +4% |
| tap: filter off blocked (ms) | 401 | 365 | +10% |
| tap: state parks on (ms) | 327 | 339 | -4% |
| tap: state parks on blocked (ms) | 334 | 300 | +11% |
| tap: state parks off (ms) | 224 | 212 | +6% |
| tap: state parks off blocked (ms) | 316 | 259 | +22% ⚠ |
| tap: open place (ms) | 15 | 13 | +15% |
| tap: open place blocked (ms) | 0 | 0 |  |
| tap: back from place (ms) | 297 | 291 | +2% |
| tap: back from place blocked (ms) | 472 | 386 | +22% ⚠ |
| tap: journeys tab (ms) | 16 | 13 | +23% |
| tap: journeys tab blocked (ms) | 0 | 0 |  |
| tap: open journey (ms) | 79 | 72 | +10% |
| tap: open journey blocked (ms) | 0 | 0 |  |
| tap: back from journey (ms) | 260 | 249 | +4% |
| tap: back from journey blocked (ms) | 410 | 358 | +15% |

By host: sachinwankhede.github.io 147 req / 3805 KB; thumb.wikimedia.org 46 req / 348 KB; fonts.gstatic.com 14 req / 185 KB; server.arcgisonline.com 40 req / 175 KB; tiles.openfreemap.org 4 req / 48 KB; fonts.googleapis.com 2 req / 1 KB;  6 req / 0 KB

### Initial Places-page load stages (observational)

Each run starts in a fresh browser context with service workers blocked; the Chromium process is reused, and the origin/CDN may already be warm. Phone runs use the same 4x CPU, 1.6 Mbps, 150 ms profile as the other measurements. These are descriptive p50/p95 timings, not regression thresholds. App, DOM, map-state, and photo-hold timestamps are observation/poll times; map tile response timing is from Resource Timing. Cross-origin timing data is not used to infer asset sizes.

Requested runs: 5; completed: 5; failed: 0.

| Stage | Samples | Failures / missing | p50 (ms) | p95 (ms) | Measurement |
|---|---:|---:|---:|---:|---|
| DOM interactive | 5 | 0 | 662 | 688 | Navigation Timing |
| DOMContentLoaded | 5 | 0 | 662 | 688 | Navigation Timing |
| Load event | 5 | 0 | 663 | 689 | Navigation Timing |
| First contentful paint | 5 | 0 | 247 | 287 | Paint Timing |
| App data ready | 5 | 0 | 553 | 583 | 20 ms poll of window.__M.ecoIds() |
| Initial cards in DOM | 5 | 0 | 553 | 583 | 20 ms DOM-state poll; first populated #cards card |
| Map style ready | 5 | 0 | 553 | 583 | 20 ms poll of window.__M.styleReady |
| First map tile response | 5 | 0 | 658 | 681 | Resource Timing responseEnd for a tile URL |
| Map loaded | 5 | 0 | 1809 | 1833 | 20 ms poll of MapLibre map.loaded() |
| Photo hold released | 5 | 0 | 1809 | 1833 | 20 ms poll of window.__M.photoGo |
| First visible photo loaded | 5 | 0 | 1829 | 1875 | Image load event for a photo intersecting the viewport |
| First visible photo decoded | 5 | 0 | 1855 | 1899 | HTMLImageElement.decode() resolution |

Long tasks through the first visible photo decode (or photo-hold release / map loaded when no visible photo decoded): 5 samples, 0 failures. Count p50/p95 11/11; total duration 1352/1370 ms; blocking time over 50 ms 802/820 ms.

### Navigation readiness (observational)

Cold open is the first route after loading the base page in a fresh browser context; warm open returns to the map and reopens the route in that same context, allowing app-level data reuse. Service workers are blocked. Place readiness requires its visible heading and food-web nodes; food-web readiness requires a visible graph with nodes and a hidden loading indicator. Species selection is measured from a synthetic node click to the selected-node state. These p50/p95 values are not compared with history or used to raise regression warnings.

| Route phase | Ready samples | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| place cold open | 5 | 56 | 58 |
| place warm open | 5 | 64 | 166 |
| food-web cold open | 5 | 100 | 102 |
| food-web warm open | 5 | 195 | 290 |
| species selection | 5 | 228 | 230 |

Median resources observed during each phase (requests / KB reported by Resource Timing; KB can be 0 for cache hits or cross-origin resources without timing access):

| Route phase | Resource class | Requests | KB |
|---|---|---:|---:|
| place cold open | web data | 1 | 5 |
| place warm open | none recorded | 0 | 0 |
| food-web cold open | web data | 1 | 5 |
| food-web warm open | none recorded | 0 | 0 |
| species selection | web data | 1 | 184 |
