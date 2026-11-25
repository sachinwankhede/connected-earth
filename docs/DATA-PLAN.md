# Data plan (15 Nov 2026)

Part of #887. Follows `docs/DATA-AUDIT.md`. Owner, 15 Nov: replace the audit, add the plan, "start from 3 and 4 first". The plan removes causes, not cases: stable identity (C), one transactional writer (A), one place for each rule (B), derived data that knows its inputs (D), and CI that cannot hide a failure (F).

## Principles

1. **Stable identity.** Every entity is keyed by its id (the place id, the species `sid`). A title, a name or a category is an attribute, never a key.
2. **One writer per file family, transactional.** Files and their index change together, or not at all. A writer that removes a thing removes everything derived from it in the same call.
3. **One home for each rule.** Statuses, ranges, retry windows and relationships live in one module in `lib/` that the writers and `build/validate_data.py` both import. No number or list is typed twice.
4. **Derived data records its inputs.** An outline, a food web or a story stores what it was built from; a mismatch counts as stale.
5. **CI fails loudly.** A crash is a failure, every test runs, and a check for each cross-file rule exists.
6. **The data layer keeps itself consistent (rule 10).** The app tolerates gaps; fixes go into jobs and validators, never into a hand edit of data and never into a looser validator.

## Order

The owner's order: **3 and 4 first.** Steps 1 and 2 are listed because 3 and 4 lean on them (see "Concerns").

| # | step | layer | owner action |
|---|---|---|---|
| 3 | Key place pictures by place id | data format, build, app reader, jobs | none (done 16 Nov: the data was keyed by id already; the app reader now registers and reads `place:<id>`, #969) |
| 4 | One writer for place pictures; retire the `data-photos` overlay | `lib/`, 7 jobs, workflow | the workflow change (`.github/**`) |
| 1 | CI hardening: `pipefail`, job tests by glob, orphan-picture check | `ci.yml`, validators | merges `ci.yml` |
| 2 | Contracts module: photo statuses, retry windows, story words and characters | `lib/` | none |
| 5 | Derived data records its inputs; a stale report, then a stale check (outlines, food webs, stories) | build, validators | none |
| 6 | Point-versus-outline check in `validate_data` (inside the outline or within a few km, and inside the state) | validators | none |
| 7 | Limit per-place species overrides (`name`, `wiki`) unless justified | `species.py pack`, validators | none |
| 8 | Data health report: per dataset coverage, validity and age; thresholds only where the owner names one | `build/data_quality.py` | thresholds, if any |

## Steps 3 and 4 in detail

**Target.** `photos/places/places.json`, `missing.json`, the retry ledgers and `places_large.json` are keyed by place id. The Wikipedia title becomes a field (`wiki`), no longer the key. One module, `lib/place_photos.py`, is the only code that adds, replaces or removes a place picture:

- `put(place_id, file, credit, ...)` stores the picture, its larger copy slot and its list entry together and clears the place from `missing.json` and the ledgers;
- `remove(place_id, reason)` removes the file, the larger copy, the list entries and records the place as missing with the reason (this retires `photos.prune_large` and the latent gap in `droppictures places`);
- `miss(place_id, status, ...)` records a miss with one retry policy, replacing the four per-job ledgers with one ledger keyed by place id with a `source` field;
- every write goes through a temporary folder and `os.replace`, so a killed job leaves the old valid state or the new valid state, never half.

The seven writers (`photos`, `commonsnearby`, `commonscategory`, `commonsplacephotos`, `openverseplaces`, `fixcoords`, `droppictures places`) become callers of it, one per pull request. The `data-photos` overlay (copying `photos/places/` from the open batch branch) is removed: each run starts from fresh main and does its whole job again, so a run can be repeated with the same result.

**Phases, each a small pull request, each green on its own.**

1. *Design item and `lib/place_photos.py` with its tests* (no behaviour change; nothing calls it yet). Includes the id-keyed format reader that accepts both shapes.
2. *Consumers accept both shapes:* `build/validate_data.py`, `build/pages_payload.py`, `build/promote_check.py`, `build/data_quality.py`, `src/app/data.js` (it already normalises the legacy list into an entity-keyed registry in memory) and the tests and fixtures that read them. The app tolerates both until phase 4 (rule 10, so an app pull request never waits for a data job).
3. *Migration as a data job:* a manual workflow `data-photos-rekey` that rewrites the files from title keys to place-id keys, splits the 5 shared titles (the places that share one record), prints a before and after table, and opens one data pull request. It runs with no open photo pull request and with the photo workflows paused (see Concerns). Validators must pass before and after; the round trip back to title keys must equal the old files for every unshared place.
4. *Move the writers, one per pull request,* smallest first (`droppictures places`, `fixcoords`), then the pass jobs, then `photos.py` last (it owns the batch and the overlay). Each uses `lib/place_photos.py` and loses its own `json.dump`.
5. *Remove the overlay and the old shape:* `data-photos.yml` stops copying from the branch (owner-merged), the readers drop the title-keyed shape, `prune_large` goes.
6. *Validators:* orphan files in `photos/places/`, one id per entry, no two places with one record, larger copy follows picture, all by id.

**Done when:** no job writes `places.json`, `missing.json`, a ledger or `places_large.json` except through `lib/place_photos.py`; the 5 shared titles no longer collide; the 9 orphan files and the 8 pictures without a larger copy are resolved by the migration or by the job; `droppictures places` cannot leave a larger copy behind; a killed job leaves a valid state (tested).

## Concerns (for the owner)

1. **3 and 4 are built on a net with holes.** CI can go green when `validate.py` crashes, and five job tests (including `droppictures`, `largephotos` and `gbifphotos`, jobs that touch pictures) never run. If 3 and 4 go first, step 1 should run alongside them: it is small, independent, and it is the one change in this plan that touches `ci.yml`, so it needs the owner's merge. Without it a broken migration or writer can look green.
2. **The format change reaches the app.** `src/app/data.js`, `build/pages_payload.py` and the service worker cache read these files, and the first-view and payload budgets apply. That is why the readers accept both shapes first (phase 2) and the format changes second (phase 3); the budget checks and `perf-ab` are read on each app change.
3. **The photo jobs must be quiet during the migration.** An open photo batch, or the daily `data-photos` run (which starts from the open batch branch), would bring back title keys or delete the migrated files. The migration needs either a window with no photo pull request open or the schedule paused; pausing a schedule is a `.github/**` change for the owner. The category pass stays off until step 4 anyway (it matches by name, #890 and #892).
4. **The migration is data, so a job does it, not an agent.** It opens a data pull request with the before and after table, the 10-item spot check and the round-trip proof; the agent merges only on a green `gate`.
5. **Size.** About eight small pull requests across `lib/`, seven jobs, the build, the app reader and one workflow. The first is a design item on #887 before any code (CLAUDE.md: discuss the design before building a job or workflow).
6. **What stays out.** Species pictures keep their title-keyed lists for now (6 parallel dictionaries keyed by wiki title is the same disease and is the next item after step 4; it is not mixed into this one). Pictures that are wrong in content (Fisherman's, Olallie, `gulf`) are fixed by the job that stores them through the new writer, not by hand.
7. **Open decisions that are not 3 and 4 (settled 15 to 17 Nov).** Pictures credited to "unknown author": a repair step in the weekly picture jobs (#1057); the health report has no thresholds (17 Nov); `sdponca` (a duplicate of Nebraska's Ponca State Park) was removed in #924.

## Place pictures: what we learned (15 Nov, #887, #908)
These are the traps behind the rules; `docs/ARCHITECTURE-DATA.md` ("Place pictures") says how it fits together.

1. **Key by identity, not by a name that can repeat.** Wikipedia titles were the key, and two places can share one (Harriman, Village Creek); a picture could land on the wrong place. Keys are place ids now, and a shared title is a validator error.
2. **One writer for everything that must agree.** Five jobs each wrote their own list and a killed run left a list row without its file or a larger copy of a picture that was gone. `PlacePhotos` writes files first and lists last, and `check()` finds any disagreement.
3. **Refuse at the writer, not in each job.** A CC BY picture with no author got in because nothing refused it. `put()` now raises; the Commons name lookup stays in the job because it needs the network.
4. **The author comes from Commons, not the uploader.** Take the Artist or Attribution field; use the uploader only when the credit says "own work". An email, a talk-page stamp, an "original uploader" sentence or a web address is cleaned to the name or counts as no author (`lib/author_clean.py`).
5. **Never loosen a validator to get green.** Fix the data job; a warning that only flags known data becomes an error once the data is fixed (shared titles, 15 Nov).
6. **Verify a "probable duplicate" before removing a place.** `sdponca` and `neponca` were the same park (same name, 0.4 km, same title); removal re-checks name and distance in the job and the owner decides first.
7. **Add a source as a function plus a stub, never a new job.** The contract test holds every source to the same rules, so a new source cannot skip the author or licence rule.
8. **Tests that patch a function patch it where it is used.** Moving a helper into `lib/` broke tests that patched the old job module; patch the `lib/` module.
9. **Do not poll the live site.** Fetching it is disallowed (robots); read data and CI instead.
10. **Quiet by design.** Retry holds (30 days) keep a weekly run silent once a place was tried; skipping the PR to save noise would lose the retry notes, so no minimum count.

## Species pictures: the same treatment (owner, 15 Nov, #934)
Owner: "Same treatment with one id, one writer, one acquire job, one author rule" and, on shared titles, "Per sid". Measured on main (15 Nov): 5,623 species rows, 5,156 wiki titles, 151 titles shared by 618 rows; pictures are keyed by wiki title in 6 lists (`species`, `species_hosted`, `species_metadata`, `species_large`, `species_medium`, `species_missing`), 4 ledgers (`species_commons_tried`, `species_openverse_tried`, `species_inaturalist_tried`, `species_gbif_tried`) and 7 jobs. 4,865 hosted, 4,863 with both copies, 267 recorded as no photo, 12 CC BY rows with no author, 272 dirty authors.

**Decisions.** Key: the species `sid` (the Latin-name slug), one entry per sid, so each species is checked and credited on its own (a title shared by two sids gives each sid its own entry; a shared title is no longer a collision). Writer: `lib/species_photos.py` (`SpeciesPhotos`, the same methods as `PlacePhotos`: put / put_large / put_medium / remove / miss / note_tried / commit / check / repair), files first, lists last. One acquire job `speciespictures` with a function per source (Commons, Openverse, iNaturalist, GBIF; `lib/species_sources.py`, like `place_sources.py`). One author rule: `lib/author_clean.py`, applied by the writer; `put()` refuses CC BY / BY-SA without an author; the validator makes a dirty author an error.

**Phases (each a small pull request, green on its own).**
1. This design and `lib/species_photos.py` with tests (nothing calls it yet; reads both shapes).
2. Consumers accept both shapes (`build/build.py`, `build/pages_payload.py`, `build/validate_data.py`, `build/promote_check.py`, the app reader, fixtures); rule 10, so no app pull request waits for a data job.
3. Migration as a data job: re-keys the lists to sid, ledgers 4 to 1 (`photos/species_tried.json`), prints a before and after table and the round trip, one data PR. Species schedules stay paused (they are).
4. `speciespictures` acquire job; the 7 old jobs and their workflows retire after one good run; `largephotos`, `hostphotos` fold into it as `put_large`/`put_medium`.
5. Author rule for species: `data-dropunnamed` for the 12 CC BY rows with no name, `cleanauthors` extended to species (272), validator error.
6. Validators by sid: orphan files, larger and medium copies follow the picture, one entry per sid.

**Owner-merged parts:** workflow changes (`.github/**`). Everything else the agent merges on green `gate`.

## Species pictures: what we learned (15 Nov, #934)
`docs/ARCHITECTURE-DATA.md` ("Species pictures") says how it fits together; these are the traps the migration met.

1. **A Wikipedia title is not an identity.** 151 titles were shared by 618 species rows (mostly non-organisms such as Rain), so title-keyed lists gave one picture and one credit to many species and made any per-species check impossible. Keys are species ids; the shared picture is stored once because its file name is a hash of its bytes (a copy per species would not fit the larger-copy budget).
2. **Old file names do not survive a re-key.** Files named after titles had to keep their names in the migration (nothing is renamed on disk), and new files are named by hash; a validator that expects `<sid>.webp` would fail on every old file.
3. **Refuse bad rows at the writer, then clean the data before the validator turns strict.** The migration found 6 CC BY pictures with no named author left (12 were counted at the start); they were removed before the migration, and `put()` now raises so none can come back.
4. **Dirty authors stay a warning until the cleaning job has run.** 272 stored authors were counted before the migration (the validator reports 292 on the by-id rows now, because rows that shared a title are now counted once per species); `cleanauthors` is to be run over the species rows (phase 5), after which the check becomes an error, as it did for places.
5. **A new shape needs its validators tested against the new shape, in a dry run of the whole migration.** Twice a validator written for the old schema failed the migration pull request: the `photos/species_missing.json` schema (a plain reason per title; the new rows are records) and `photo_registry validate` (it read `species.json` and `species_hosted.json`). The migration's dry run now runs `build/validate_data.py` and `lib/photo_registry.py validate` on the migrated tree, and every new shape ships its validators and their tests in the same pull request as the writer.
6. **Remove dead branches when the old shape is gone, not before.** Validators and readers kept both shapes during the migration; once the title lists were removed, the title-keyed checks, the `species-missing` schema and `photo_registry.safe_species_asset` could never run and were deleted. The reader `lib/species_pics.py` and the frozen old-shape test fixture stay on purpose, and the old acquire jobs stay until their workflows are retired.

## One ledger for every kind of picture (25 Nov, #1183)
Species, places, journeys and nodes keep the retry ledger in the same shape, `{id: {source: 'YYYY-MM-DD'}}` (`photos/species_tried.json`, `places_tried.json`, `journey_tried.json`, `node_tried.json`), held `contracts.SOURCE_RETRY_DAYS` (30). The source `copy` records a larger copy that could not be made, `author-repair` an author lookup that found nothing. Each writer checks the shape (`CreditRepair.ledger_errors`); the four jobs share flags, the time budget and the `more: N` / exit 3 contract (`lib/runbudget.py`). A missing node ledger file is read from `node_missing.json`.

## Journey pictures: by journey id (owner, 15 Nov: "Own")
Today a journey has no picture of its own: its cover is the picture of the title in its `imgwiki` (a species such as "Osprey", or "Saharan Air Layer" for the two flow journeys) and each end shows its place's `imgwiki` picture, all looked up by title (`PHOTOS[title]`, `src/app/journeys.js`). Decision: the same treatment as places and species. A journey cover is its own picture row **keyed by journey id** (own file, credit and licence), found by the same acquire job (a journey strategy there, not a new job), written only through one writer (a `lib/journey_photos.py` modelled on `PlacePhotos`/`SpeciesPhotos`), with the same author rule and one validator. The ends of a journey use the place pictures by place id. The build and the app stop looking journey pictures up by title. Phases: 1 writer and reader (nothing calls it), 2 build/payload/validator read it, 3 migration of the 19 cover pictures (a one-off job, a manual workflow, owner-merged), 4 the acquire strategy, 5 the app reads the cover by journey id. Starts after the species migration (#934) is merged.

## Credits: one record shape for every picture and outline (owner, 16 Nov, #976, #977)

- **One shape.** A credit record is the same for places, species, journeys, non-species nodes (#976) and outlines (#977): `source`, `licence`, `licence link`, `page` (where it was found), `built` (when we stored it) and `checkedAt` (when the source was last confirmed). `author` is part of it for a picture and optional for an outline (the credit for an OpenStreetMap outline is one shared line, once the licence is confirmed). Author text follows `lib/author_clean.py`.
- **Files and app keys stay per kind.** Each kind keeps its own file family and writer; the app keys are namespaced (`place:`, `species:`, `journey:`, `node:`) so an id of one kind never meets an id of another.
- **No expiry date on a found picture.** We host our own copies and the licences we accept do not run out, so the record carries `checkedAt` and no `expires`; a date is enough to add a re-check later without a migration. The one risk is Wikimedia Commons deleting a file after the fact (a licence problem): if the owner wants it covered, a small monthly sample re-check is the way, not an expiry on every picture. The retry expiry of a *missing* record (`expiresAt`, `lib/photo_registry.py`) stays: it is how a job knows when to try again.
- **Sizes (owner, 25 Nov, #1188): no 96 px step.** The first fetch is shrunk straight to the 192 px WebP and that file is the stored picture: species `photos/species-md/<f>.webp` (`f` = first 12 hex digits of the sha256 of that file; `species_medium.json` is written with it), journeys `photos/journeys/<id>.webp` (same name as before), nodes `photos/nodes/<hash>.webp` (unchanged). The 400 px copy (species `species-lg`, journeys `journeys-lg`) still comes from the larger download; if it cannot be made the app shows the 192 px picture and the 30-day copy hold applies. Old data (96 px files in `photos/species/`, 96 px journey covers) keeps validating and building until the migration `jobs/drop96px.py` (a data job runs it; `--dry` lists what changes). Places are unchanged.
- **Not yet done:** `checkedAt` on species and journey records (places have `checkedAt` and `fetchedAt`), the node record file (#976) and the outline record (#977) use this shape from the start.

## What this plan does not do

No database or server. No new photo source before the writer exists. No more per-job regular-expression tightening as a substitute for identity checks. No raising of a threshold to turn a check green. No `species.py pack` as a silent rewrite of everything inside unrelated jobs.
