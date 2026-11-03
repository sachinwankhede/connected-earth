# Data and loading design (decided 2026-11-01 with the owner)

Why: the page is one file with all places, outlines and the diagram library inside it (about 1.8 MB, 830 KB of it places data). That costs about 650 bytes per place, so 10,000 places would be about 6.5 MB inside the page. The app must keep working as places are added, so code and data are separate and data is loaded in pieces.

## Rules
1. **The page holds code only** (app, styles, start screen). No places data, outlines or diagram library in it.
2. **First-screen places file:** per place only id, name, position, kind and region (about 40 to 60 bytes). Split by continent so a phone fetches only what it shows.
3. **Detail on demand:** card text, pictures, story and food web load when a card is near the screen or a place opens (food webs already do: `api/`).
4. **Outlines:** the country outlines (145 KB raw) draw the home map, so they stay up front. The US state outlines (125 KB raw) are only needed once you go into the US, so they get their own file loaded then.
5. **Search has its own file,** fetched in the quiet time after the first screen. Search shows "getting ready" until it arrives (owner agreed).
6. **Offline:** not a promise for all places. The shell (page, icons) and the places you opened are kept by the service worker. Do not add a background download of everything (owner decision).
7. **Nothing is written by two jobs.** Each data file has one job that produces it.

## Steps (one item and one pull request each, measured on the phone profile; skip the measurement only when the change is clearly safe and measuring would take long, the owner agreed this call can be made case by case)
Order changed after measuring: the places data is the big piece (about 830 KB raw), the state outlines only about 125 KB raw (roughly 0.2 s on the phone profile), so places data goes first.
1. Places data split into a first-screen file plus detail on demand (#228; replaces #187).
2. Search file (#229).
3. US state outlines on demand (#227).
Also on the list: diagram library (D3) on demand (#186).

## Trade-off
Moving data out of the page means a short wait the first time you open a region, a place or search, instead of a longer wait at the start. The first screen must never wait for these.

## Photos are data too (added 2026-11-02)
Findings: to open one place the app downloads a list for all 4,802 species (644 KB raw, 176 KB gzip) and, at start, a list for all 1,144 places (601 KB raw, 119 KB gzip). A place needs about 30 species entries.
Rules:
1. **A picture entry belongs to the thing it shows.** A place's own file carries the entries of its own species (about 5 KB); a card's picture entry travels with the card data. No global list is needed to open a place (#237).
2. **Our own small copies.** A GitHub job downloads each species picture once, shrinks it (about 96 px WebP), keeps credit and licence, and writes one packed file per place (#238). Credits stay in the metadata files and are still shown.
3. **Short, stable addresses** (by id or hash), not long Wikimedia paths repeated twice per entry.
4. **Global lists are only for search or review jobs,** never read to open a place.
5. The photo jobs keep one writer per file and open pull requests that the owner merges.

## Data contract: a static API (added 2026-11-02, item #241)
Principle: everything the app shows comes from data we host. The app reads it through **one data-access module**, never by fetching files from scattered places in the code. The only external reads left are the base map (vector tiles, satellite imagery, elevation) and the links to Wikipedia pages that people open themselves. No runtime lookups of text or pictures from Wikipedia or Wikimedia.

The site is static, so each "API" is a file with a fixed shape. If a server is ever needed, only the module changes.

**Folder today (#305, 2026-11-03):** the build's published data folder is `api/` (it was `webs/`; the build deletes a stale `webs/`). For now the files keep their old names inside it: `api/<id>.json` (one place), `api/species-index.json`, `api/species-pictures.json`, `api/species/<id>.json`. The per-place files move to `api/places/` together with the manifest (#241); the table below is the target layout.

| Call | Static file | Notes |
|---|---|---|
| Manifest | `api/manifest.json` | version and content hash of every file below; the app and service worker use it to know what changed |
| List places | `api/places/index-<region>.json` | id, name, position, kind, region, tier, flags; one file per continent (more shards when needed); paged cards come from `api/places/cards-<region>.json` |
| Get place | `api/places/<id>.json` | food web, story, why it matters, sources, and the picture entries of its own species |
| List species | `api/species/index.json` | id, names, group; paged files when large |
| Get species | `api/species/<id>.json` | description, picture entry, which places have it |
| Search | `api/search/meta.json`, `w-<two letters>.json`, `rows-<n>.json` (pilot: `api/search-pilot/`) | #260 step 1 (2026-11-03, build only, the app does not read it yet). Word list in buckets by first two letters: sorted words, each with delta-coded place numbers (page order of that build); rows files hold 256 places each as `[id, name, place, lat, lon, continent, first state]`, enough to show a result and fly to it with no region loaded. Words: name, place line, short, kind, species common and Latin names, environment words; accents and apostrophes dropped. A query word matches by prefix. The app reads it since #260 step 2 (falls back to the species-list scan if the files cannot be fetched). |
| Related places | in Get place | neighbours precomputed by the build, not computed in the browser |
| Pictures | `img/species/<hash>.webp`, packed per place | our own copies with credit and licence (item #238) |

**Places files, step 1 (#228, 2026-11-03):** the build now also writes `api/places/index.json` (id, short, lat, lon, kind, icon, level, tier, auto, park, cont, country, countries, states; a list in page order) and `api/places/cards.json` (everything else of the light place, keyed by id: name, place, blurb, imgwiki, idx counts, side). Merged they equal the light place the page still carries (`tests/data/places_split_test.py`); any new field goes to the cards file unless added to `INDEX_FIELDS` in `build/build.py`. The pilot build writes `index-pilot.json` and `cards-pilot.json` (a different place set; two builds never write one file); each build deletes other files in `api/places/`. **Step 2 (2026-11-03): the app reads them.** A small script in the head fetches both files at once; the app starts when both have arrived (the first render waits for both) and puts each place together as index + cards. `DATA.ecos` is no longer in the page (main page 1.25 MB to 0.59 MB raw). The service worker precaches both main files. If they do not arrive the start screen says so with a link to try again.

Rules: ids are stable and short; files are versioned by the manifest; each file has one writer job; the service worker caches by manifest hash. Filters that the file layout cannot answer (for example kind and country together) are done in the browser over the loaded index.

## Compute at build, read at runtime (added 2026-11-02)
Rule: nothing that can be worked out ahead of time is worked out on the phone. The build (or a job) computes it, writes it as data, and the app only reads and draws. Runtime search, scans over every place, and layout simulations are the things to remove.
To precompute, in order of cost on the open path:
1. Food-web layouts: node positions stored per place (##259).
2. Search: a ready-made word index (##260).
3. Region, kind and park lists with counts (##261).
4. Related places (#252), species counts and link counts (#258), badges and rankings (##262).
5. Journeys per place (##263) and species to places (#253).
The app then needs no scan of all places and no simulation to show a screen.

## Folder layout (added 2026-11-02, item #267; all stages done)
Code, data and jobs are kept apart, so a change can say which of the three it touches.
- `src/`, `build/`, `tests/`, `fonts/`: code.
- `data/places/<id>.json`: one file per place (written only by data jobs). `data/journeys/links.json`: the order of places and the journeys between them. `data/species/species.json`: the species table; `data/species/about.json`: species descriptions. `data/text/summaries.json`: one-sentence park summaries. `data/outlines/`: place outlines. `data/geo/`: country, state and land outlines.
- Pilot places are in `data/places/` too, marked `"stage": "pilot"` (absent means main; `tier` stays overview/detailed). Their order is `data/journeys/pilot-order.json`; the main order is `links.json`. The main build loads the places listed in `links.json`; the pilot build adds the pilot list. Promoting a place drops `stage` and adds it to `links.json`; the file does not move. (`data-auto/` was folded in on 2 Nov, item #267.)
- `photos/`: place photos, species picture references, our hosted species pictures (`photos/species/`) and their credits.
- `jobs/`: job scripts and their own state (queue, names, reports, park lists). `lib/`: code shared by the build and the jobs (the photo registry). Anything the build reads lives in `data/` or `lib/`, never in `jobs/`.
Nothing the build reads may live in the jobs folder.

## No web reads at run time (owner rule, 2 Nov)
The app reads everything it shows from data we host. The only accepted outside reads are the base map tiles (and the map style and fonts they need). There is no fallback to another site when our copy is missing: a missing species picture shows the placeholder, and a data check fails the pull request when a listed picture has no hosted file or credit. A browser test (item below #238) fails on any other outside request.

## Tests and CI by kind of change (added 2026-11-02, items #269 and #272)
Tests live in `tests/app/` (browser and app code), `tests/data/` (data files, no browser), `tests/jobs/` (job scripts and the CI rules) and `tests/perf/` (speed harness). `build/ci_changes.py` decides what a change needs: app changes run everything; data changes run validation, the pack check, build, size budgets, data tests and one smoke test; job changes run only the job self-tests; docs, notes, data-job workflows and job state files run nothing. The `gate` job always runs and is the one check to require.

## Species descriptions: one small file each (added 2026-11-02, item #276 step 1)
The build writes `api/species/<id>.json` ({"t": text}) for every species that has a description, and the app asks for that one file when a species sheet opens. The id is the species id (`sid`); the app derives it from the Latin name with the same rule as `build/species.py` (`slug`), and the build refuses a description whose id is not that slug. The bulk `api/about.json` is gone. The source table `data/species/species.json` is unchanged; moving the source itself to one file per species is step 2.
