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
| 3 | Key place pictures by place id | data format, build, app reader, jobs | none |
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
7. **Open decisions that are not 3 and 4.** The 98 pictures credited to "unknown author" (licence doubt, owner); whether the health report needs thresholds; how to treat `sdponca` (a duplicate of Nebraska's Ponca State Park).

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
10. **Quiet by design.** Retry holds (90 days) keep a weekly run silent once a place was tried; skipping the PR to save noise would lose the retry notes, so no minimum count.

## What this plan does not do

No database or server. No new photo source before the writer exists. No more per-job regular-expression tightening as a substitute for identity checks. No raising of a threshold to turn a check green. No `species.py pack` as a silent rewrite of everything inside unrelated jobs.
