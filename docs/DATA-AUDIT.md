# Data audit (15 Nov 2026)

Owner, 15 Nov, in a session: "data correctness, integrity, completeness, stability, freshness is a big issue which we keep struggling ... it feels like patch work bandaid everywhere ... we need to take a step back and figure out a better plan." Then "Yes" to a read-only audit first. This is that audit. It changes no code and no data.

## How it was made

Read-only. For each dataset I listed which `jobs/*.py` mention its files and which `build/` or `lib/` code checks it (by searching for the paths), then read the writers and checks that mattered. It is a map, not a proof: a job can touch a file without a path string, and "no check found" means I found none in `build/validate*.py`, `lib/` or `tests/data/`.

## The datasets, who writes them, who checks them

| dataset | writers (jobs) | checks (build / lib) | gap found |
|---|---|---|---|
| Place pictures (`photos/places/`, `places.json`, `missing.json`) | 13: photos, commonsplacephotos, commonsnearby, commonscategory, openverseplaces, gbifphotos, inaturalistphotos, speciesphotos, commonsphotos, droppictures, fixcoords, largeplacephotos, openversephotos | `validate_data`, `photo_registry`, `promote_check`, `data_quality`, `pages_payload` | Rules live in several jobs, not in one shared writer (see 1) |
| Larger place pictures (`places-lg/`, `places_large.json`) | `largeplacephotos`; `photos` (since #880) | `validate_data` (strict since #873), `budget`, `pages_payload` | Before #880 only one job knew they exist; `droppictures places` still does not (see 2) |
| Species pictures (`photos/species*`) | 7 jobs | `validate_data`, `budget`, `data_quality` | `droppictures` handles the larger copy for species, copied by hand |
| Place files (`data/places/*.json`: text, story, coordinates) | 11 jobs (stories, names, summaries, fixcoords, sync) | `validate.py`, `validate_data` | Text length range is in `validate.py` and was unknown to the writer until #885 |
| Coordinates (`data/geo/geo.json`, point in each place file) | `fixcoords` only | `validate.py` (range), `validate_data` (shape of `geo.json`) | "A point lies inside its own state" is checked only inside `fixcoords`' own audit, not in CI (see 3) |
| Species table, diets, journeys, outlines | build and a few jobs | `validate_data`, `diets`, `journeydata` | no gap found at this depth |
| Status words and retry dates (`photo_registry`, `*_tried.json`) | 11 jobs | schema in `build/schemas/`, `lib/photo_registry.py` | the schema and `PERMANENT` were two lists that drifted (#877) |

## Findings

1. **The same rule is written in several places.** Examples: the story length range (`build/validate.py`, and from #885 the writer and the batch, sharing constants but with a test, not an import, tying them to `validate.py`); the allowed photo statuses (the schema and `PERMANENT`, which drifted and failed the daily batch, #877); "a larger copy belongs to a stored picture" (`validate_data`, `largeplacephotos`, `photos`, `droppictures` for species). Each copy was right when written; they drift.
2. **A latent copy of the Arrowhead bug.** `jobs/droppictures.py` removes species pictures and their larger copies together, but its `places` mode removes place pictures and does not touch `photos/places-lg/` or `places_large.json`. The next run of it fails `data checks` exactly as #876 did. (Not fixed here: it belongs in the plan below, not in another patch.)
3. **Coordinates have no CI guard.** `fixcoords` finds a point outside its own state and moves it, but nothing in CI fails a pull request that brings one in (for example a regenerated place). The 17 wrong points of 13 to 14 Nov were found by a job run, not by a check.
4. **Failures show up at the end.** The writer does not know the final validator's rules, so a bad draft or file travels through the judge, the batch or the photo run and fails the pull request: two thin story drafts failed a whole batch (#885); a stale larger copy failed the daily photo batch (#880); a skipped ancestor skipped the judge and batch silently (#882). Two of the three were also hidden by how the CI log reads (#881).
5. **Freshness and completeness are barely measured.** `build/data_quality.py` prints four indicators with no thresholds (photo metadata present, outline coverage, journey endpoints, species attribution unavailable). There is no per-dataset view of how many places have a verified coordinate, a picture, a larger copy or a story, or how old each is. Place pictures all carry `checkedAt`, but nothing reads the age.
6. **Repair is done by hand and by patch.** The fixes this week (#873, #877, #880, #885) each closed the case that failed. That was right for each failure and is the pattern the owner is describing.

## What went wrong, 13 to 15 Nov, by cause

| incident | cause class |
|---|---|
| 17 coordinates outside their own state; species built for the wrong place | no guard on a cross-file rule (3) |
| `wrongpage` status failed the daily photo batch (#876, fixed #877) | rule in two lists (1) |
| stray unlisted larger picture turned `data checks` red (#870, #874) | list and files written separately |
| Arrowhead larger copy left behind (#876, fixed #880) | a writer unaware of a derived file (2) |
| two thin story drafts failed the story batch (fixed #885) | writer did not know the final rule (4) |
| judge and batch skipped when research was 0 (#882) | CI condition, silent skip (4) |
| data job showed a browser error instead of the real failure (#881) | CI log hid the cause (4) |

## Proposed plan (small steps; each is useful alone)

1. **One contract per dataset.** One module in `lib/` per dataset (place picture, larger copy, place text, coordinate) holding its fields, allowed values, ranges and relationships. Writers and `validate_data` import it; no number or status list is typed twice. First candidates: photo statuses and the picture-to-larger-copy relationship.
2. **One writer for place pictures.** Add, replace and remove go through one function that also keeps the larger copy and list entry in step; the 13 jobs call it. This retires `prune_large` as a patch and closes finding 2 for good.
3. **Writers check their own output.** Every data job's last step runs the checks that apply to what it wrote, and fails its own run, so a bad file never becomes a pull request.
4. **A coordinate check in CI.** Move the "inside its own state" rule from `fixcoords` into `validate_data` (using `data/geo/geo.json`), so CI, not a job run, is what catches it.
5. **A data health report.** Grow `data_quality.py` into a per-dataset table: coverage, validity, age. Keep it informational first; add thresholds only where the owner names one.
6. **An owner for each dataset.** One line per dataset in `docs/ARCHITECTURE-DATA.md`: its writer, its contract, its checks.

Order that I would take, subject to the owner: 4 (smallest, closes a real hole), then 1 and 2 together for pictures (the area with the most failures), then 3, then 5 and 6.

## What I need from the owner

- Which step to start with (my pick: 4, then 1 and 2 for pictures).
- Whether the health report (5) should have thresholds, and which ones.

## Not covered

Species names and taxonomy, the research and `gemini-stories` branches beyond the story rules above, outline generation, and the map style. Nothing here was run against live data beyond reading the files in the repository and the CI logs named above.
