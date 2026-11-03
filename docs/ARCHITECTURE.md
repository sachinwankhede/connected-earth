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
2. **Our own small copies.** A GitHub job downloads each species picture once, shrinks it (about 96 px WebP), keeps credit and licence, and packs each place's entries into the place's own file as `ph` and `phm` (#238). Credits stay in the metadata files and are still shown.
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
| Pictures | `photos/species/<file>.webp` (hosted copies; each place's file carries its own `ph`/`phm` entries) | our own copies with credit and licence (item #238) |

**Update (#313 step 4a, 3 Nov):** `api/places/index.json`, `cards.json` and the `-pilot` pair are no longer written; the app reads only `api/places/main|pilot/` (world files first, locals after). The paragraph below is the history of how they were split.

**Places files, step 1 (#228, 2026-11-03):** the build now also writes `api/places/index.json` (id, short, lat, lon, kind, icon, level, auto, park, conts, countries, states; a list in page order) and `api/places/cards.json` (everything else of the light place, keyed by id: name, place, blurb, imgwiki, idx counts). Fields the app never reads (tier, cont, country, side, ly, idx.nl) stay in the source data and are left out of both files (`NOT_SHIPPED` in `build/build.py`, #313 step 1). Merged they equal the light place minus those fields (`tests/data/places_split_test.py`); any new field goes to the cards file unless added to `INDEX_FIELDS` or `NOT_SHIPPED` in `build/build.py`. The pilot build writes `index-pilot.json` and `cards-pilot.json` (a different place set; two builds never write one file); each build deletes other files in `api/places/`. **World first (#313 step 3, 2026-11-03):** the app starts from `index-world.json` + `cards-world.json` (the 349 places that are not local; about 32 KB gzip against 80 KB for the two big files) and fetches `index-local.json` + `cards-local.json` (all 923 local places, 48 KB gzip) about 2.5 s after the map has drawn, or at once when something needs them: the local button, a search (place numbers need the full list), Near me, a link to a place that is not loaded. `Places.done` tells whether they are in; `Places.loadLocals()` fetches them once. The count of local places is written into the page by the build (`NLOCAL`) so the local button shows from the start. A page opened with a link to a place (`#pg=`, `#p=`, `#e=`) loads the local places with the first load (the link may be to one); `showPlace`, `showWeb` and `peek` fetch them first when given an id that is not loaded. Search turns place numbers into ids with the rows files. The per-state shards are not read yet (step 4 loads one region at a time). The service worker precaches the world files. **Per region (#313 step 2, 2026-11-03, build only, the app does not read it yet):** the same places also cut by region in `api/places/main/` (pilot: `api/places/pilot/`): `positions.json` (what the world map draws: the places that are not `local`; `[id, short, lat, lon, kind number, flags]`, flags 1 = auto, 2 = park), `positions-local.json`, `index-world.json` + `cards-world.json` (the non-local places in the two formats), `index-<region>.json` + `cards-<region>.json` (the local places of one region: a US state, or the continent outside the US states; today all 923 locals are in 50 states), and `counts.json` (per continent, country and state: counts as [not local, local] by kind and for parks, and the shards the region's locals are in). A place is in exactly one of world and shards; `tests/data/places_regions_test.py` checks the union against index.json and cards.json and the counts by brute force. **Step 2 (2026-11-03): the app reads them.** A small script in the head fetches both files at once; the app starts when both have arrived (the first render waits for both) and puts each place together as index + cards. `DATA.ecos` is no longer in the page (main page 1.25 MB to 0.59 MB raw). The service worker precaches both main files. If they do not arrive the start screen says so with a link to try again.

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

## What the app does with "all places" (audit for #313 step 4b, 3 Nov)
`ECOS` (the full list of loaded places) is read in about 30 places of `src/app.html`. Loading one region at a time only works if each use is served by something smaller. The uses fall into six groups:

| Group | Where (functions) | What it really needs | Served by |
|---|---|---|---|
| A. Map dots and fitting | `ecoFC`, `flagFC`, visible-in-view count, `mapFit`, fit-to-region | id, lat, lon, kind, flags, level, and region membership (`inRegion`: continents, countries, states) | positions file, **if it also carries region membership** (today it has id, short, lat, lon, kind, flags only) |
| B. Counts and browse lists | continent, country, state browse rows, per-kind counts, "N results" | counts per region and kind, with park, local and query filters applied | `counts.json` for the plain case; positions for any filtered case; search hits for a query |
| C. Card list and paging | the list built from `ECOS.filter(inRegion)`, card DOM, photo wanting | the cards of the region being listed | the shard of that region, loaded when the list opens |
| D. Near me | `nearMe` | positions of every place to rank, then cards of the nearest five | positions, then 5 cards by id |
| E. Species overlap | related places on a place page, the same species in other places, the species ties graph, the species-to-places lookup | for each species, which places hold it | **not placeable by region.** Needs the precomputed related-places (#252) and species-to-places (#253) data; today it scans every place's species list from the 134 KB gz species index |
| F. Start-up loops | species filling for all places, place dropdown options, `ECO_BY` fill, the old search-text fallback, map label de-duplication (`short` of every place), test hook `ecoIds` | mostly ids and short names | positions (id, short); species and search text come with the index and search files |

Design rules this gives (to be decided before step 4b is coded):
1. **A light directory of all places stays in memory** (positions plus region membership, about 12 to 15 KB gz). Groups A, B, D and F read it. It replaces `ECOS` for everything except card text.
2. **Cards are fetched by id**, through one function that finds the shard (region key stored in the directory) and returns a promise. Every place page, peek, card list and Near me row goes through it. This is the "not yet" guard of step 3 made the normal path, not a patch.
3. **Positions must carry region membership** (or the shard key plus enough to answer `inRegion`). This is a build change in `split_regions` and the first thing to do.
4. **Group E is a blocker, not a detail.** Region loading does not remove the scan; it makes it wrong, because a place's neighbours may live in a region that has not loaded. #252 and #253 must land first, so the app reads the answer and no longer computes it.
5. **The species index (134 KB gz) is larger than all place files together** and is only needed for group E and species search. After #252/#253 it can be dropped from start-up.
6. Tests that call `__M.showPlace(id)` or open places by link must wait for the card, so the test helpers need a "place ready" wait.

## Species shared between places, computed by the build (items #252, #253, PR A)
The app used to scan every place's species list for "Shares species with", "Also found in" and the map arcs. The build writes the answers. Since PR B the app reads related places (`rel`/`relp`) and the places of a species; it still scans for the map arcs (ties), see below:
- **In each place's own file `api/<id>.json`:** `rel` (top 10 places by species in common, `[[id, count], ...]`) and `ties` (places sharing a species found in 2 to 10 places, `[[id, [names]], ...]`). These files are shared by the main and the pilot page, so a main place keeps the main-set answer in `rel`/`ties` and, when the pilot set gives another answer (the pilot page has more places), also `relp`/`tiesp`. A pilot-only place has only `relp`/`tiesp`. The app reads `relp || rel` on the pilot page and `rel` on the main page.
- **`api/species-places/<two characters>.json` (main) and `api/species-places-pilot/`:** the places of each species found in 2 or more places, in page order, in the file of the first two letters or digits of its Latin name (`species_bucket` in `build/build.py`). Fetched when a species is selected.
- Test: `tests/data/species_links_test.py` compares all of it with a brute-force scan written the way the old browser code worked, for the main and the pilot set.

**PR B (app reads the data, 3 Nov):** "Shares species with" (place page and food-web panel) reads `rel` of the opened place's file; "Also found in" fetches `api/species-places[-pilot]/<two characters>.json` when a species is selected and fills its row when the file arrives (`#where-else`). A related or listed place that is local is waited for (`Places.loadLocals`) so the row is complete.
**Found while doing PR B:** the map arcs and the card on tapping a place (`tiesFor`: "Shares species with" under a map card, up to 8 arcs) need the ties of a place *before its file is opened*. A place file holds `ties` but a map tap does not fetch it, so the app still builds ties by scanning the species index. Options: fetch the place file on a tap; or write the top 8 ties of each place (ids, three species names, the count) where the card is (a start-up file, or a state shard once #313 step 4b exists). Until one is chosen the species index (134 KB gz) stays.
**Ties per region (D1, 3 Nov; owner chose this over a start-up file or a fetch per tap):** the map arcs and the line on a tapped map card need a place's ties before its file is open, so they are not in the place files (PR A wrote them there; they were removed again, only `rel`/`relp` stay). `api/ties/<region>.json` (main) and `api/ties-pilot/<region>.json` hold, for each place of the region, the 16 places that share most rare species (found in 2 to 10 places): the first 5 as `[id, species in common, [up to 3 names]]` (the map card), the rest as bare ids (arcs inside the view). The region is the grouping of the region place files: `world` for a place that is not local, else the US state or the continent (`region_key`). Main: 51 files, 124 KB gz in total, largest (world) 32 KB gz; pilot: 155 KB gz, largest 46 KB gz. The app (D2) fetches the file of a place's region on the first tap in it.

**D2 (app reads the ties per region, 3 Nov):** `tiesFor(id)` reads `api/ties[-pilot]/<region>.json` (region = `tieRegion(e)`, the same grouping the build uses: `world` for a place that is not local, else US state or continent). The first tap in a region fetches the file (about 32 KB gz for `world`) and then redraws the arcs and fills the "Shares species with" line of the open card (`fillPeekTies`); later taps in the region cost nothing. "Show on the map" for a species now filters by the species-places file of its Latin name, not by a scan. **The species index (`api/species-index.json`, 134 KB gz) is no longer fetched at start-up or when a place opens**; it is fetched only as the fallback when the search word index is missing (`SRCH.ok` false). The file is still built and shipped for that fallback; removing it for good is PR C.

**PR C (species index removed, 3 Nov):** `api/species-index.json` is no longer built or shipped, and the app no longer has the species-list scan (`SPIDX`, `loadSpecies`, `wantSpecies`, `fillSpecies`, `idx.sp`/`idx.q`, `e._s`). Search reads the word index (`api/search[-pilot]/`). If those files cannot be had, `srchRun` records `SRCH.failedAt` and the list filters on the card text alone; the next typed query after 30 s tries the index again (it used to give up for the whole session). "Show on the map" for a species without a Latin name now goes through the word index instead of the old scan.

**4b step 1 (positions carry region membership, 3 Nov, #313):** `positions.json` and `positions-local.json` now carry `g` (the table of distinct [continents, countries, states], 233 on the main set) and two more numbers per row: the index into `g` (so `inRegion` can be answered without the place's card) and the shard key (`world`, a US state or a continent) that says which file holds the card. The app does not read the files yet. Sizes (gz, main): positions 10.1 KB, positions-local 24.7 KB, so a directory of all places is about 35 KB gz (pilot about 42 KB). The one-fetch locals files cost about 48 KB gz; the saving of 4b is therefore smaller than first estimated and only real on visits that never open a local place.

