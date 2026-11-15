# Data audit (15 Nov 2026, second version)

Owner, 15 Nov: "data correctness, integrity, completeness, stability, freshness is a big issue which we keep struggling ... it feels like patch work bandaid everywhere ... we need to take a step back and figure out a better plan." The first version of this audit (a map of writers and checks, read from the jobs only) was rejected by the owner as superficial: it never measured the data and its plan treated one cause of five. This version replaces it. The plan that follows from it is `docs/DATA-PLAN.md`.

## How it was made

Two independent reviews, read-only, neither shown the first audit until the end: (1) a design review of the jobs, workflows, validators and docs from first principles; (2) a measurement of the committed data with short scripts (counts, cross-file checks, the repository's own validators). Nothing was changed. Limits: the clone is shallow (history starts 12 Nov), so nothing older than that can be dated; no network, so no picture was looked at and no GBIF or Commons fact was checked; state and country containment used the coarse `data/geo/geo.json` (7,916 vertices), so small misses on coasts and borders are noise; the outline test is precise. Three claims were re-checked by hand for this document: CI runs `validate.py | tee` without `pipefail`, `data-photos.yml` copies `photos/places/` from the open batch branch over a fresh main, and five job test files are not in `ci.yml`.

## The data, as it is

Both validators pass today (`build/validate.py`: 1,549 places, 0 errors; `build/validate_data.py`: 0 problems). Everything under "Violated now, caught by nothing" below passes CI.

| area | measured |
|---|---|
| Places | 1,549 (277 pilot, 1,272 main); all have coordinates and a food web |
| Place pictures | 1,317 have one, 1,309 a larger copy; 232 have none |
| Stories | 320 places (1 of 277 pilot); summary sentences: 0 of 1,549 (`data/text/summaries.json` is empty) |
| Outlines | 1,395 (154 places without) |
| Journeys | 31 places |
| Species | 5,623 rows; 5,396 hosted pictures, 204 recorded missing, 20 with no picture record |
| Time | place pictures: `checkedAt` all within 13 days (bulk re-stamp, so it says nothing about when a picture was verified); `fetchedAt` null on 1,107 of 1,316; place records have no timestamp; `data_quality.py` shows outlines as 1,126 of 1,272 when 1,395 exist and species attribution as "unavailable" when 4,934 are recorded |

## Violated now, caught by nothing

1. **Geography.** 43 of 1,334 points fall outside their own state (15 by more than 5 km; 5 lie inside another state: `sdponca`, `azlakehavasu`, `momiddlemississippi`, `wvblennerhassettis`, `deauburnheights`). 290 points lie outside their own outline, 22 by more than 5 km and 3 by more than 50 km: `metroutpond` (Maine) has a West Virginia outline, `nyrobertmoses` has a point near Schenectady and the Long Island park's outline (251 km apart), `npchannelislands` has the outline of an Air National Guard station. `sdponca` is a duplicate of Nebraska's Ponca State Park (same name, outline and picture). `whaldabra` is coded Madagascar. 237 points have one decimal place (about 10 km); 13 are whole degrees.
2. **Pictures.** 9 files in `photos/places/` are listed nowhere (`congo`, `kelp`, `ozarks`, `okarrowhead`, `wharguin`, ...). 8 pictures have no larger copy (all names with a "/"). 4 pairs of places share the same image bytes. 5 titles are shared by 10 real places (Harriman NY and ID, Village Creek AR and TX, Ponca NE and SD, Ozark NSR, Gulf Islands NS); none has a picture yet, but any fetch gives both the same one. Confirmed wrong subjects: Fisherman's (shows Marconi, California), Olallie (links the Olallieberry article), `gulf` (shows the Florida and Mississippi seashore for a Louisiana and Texas place). 17 missing names appear in no tried file.
3. **Licences (needs the owner).** 98 pictures are CC BY or CC BY-SA with the author "unknown author" (17 place, all `legacy` review status; 81 species). A BY licence requires naming the author.
4. **Species.** 20 taxon rows (`src: manual`, added 14 Nov) have no taxonomy entry and no picture record. Place nodes carry 18,458 `desc`, 1,307 `name`, 1,066 `wiki` and 226 `tl` overrides of the species table; a wrong name fixed in a place file stays as a permanent override. 36 rows are used by no place.
5. **Stories.** The 60-word story and 40-word why rule is checked by the story jobs only; `build/validate.py` counts characters (120 to 620, 80 to 520), so nothing at the data layer fails a 90-word story.
6. **Derived data is not refreshed.** `fixcoords` moves a point and leaves the outline, the food web (rebuilt later by a separate PR, #872) and the story as they were. Regeneration (`regenplaces.py`) replaces a place's nodes and keeps its story, which was written from the old species.

## Where the pipeline is shaped wrong

1. **A picture is identified by its Wikipedia title, its file by the place id.** `places.json`, `missing.json`, the four retry ledgers and `places_large.json` are keyed by title; `photos/places/<id>.jpg` by id. Two places with one title share one record. `photos.py` reuses an existing `<id>.jpg` without downloading it again, so a renamed title can attach new credit to old bytes.
2. **Many writers, no transaction.** `places.json` and `missing.json` are written by 7 jobs (`photos`, `commonsnearby`, `commonscategory`, `commonsplacephotos`, `openverseplaces`, `fixcoords`, `droppictures`), each with its own `json.dump(open(path, 'w'))`. `docs/ARCHITECTURE-DATA.md` says one writer per file; in practice that is not so. The first audit counted 13 jobs; five of them write species pictures.
3. **The `data-photos` overlay brings deleted data back.** It checks out main and copies the whole `photos/places/` folder from the open batch branch (`data-photos.yml`). Anything removed on main since the branch was cut returns. #806 was closed for this reason and the cause is still there.
4. **Concurrency groups do not protect the data.** A group queues runs of one workflow; the race is between open data PRs cut from main at different times. `places_large.json` is written by `data-photos` and `data-largeplacephotos`, which are in different groups. Place files are written by `fixcoords`, regen, `regenplaces`, promote, state, story-batch and names, each in its own group, and each runs `species.py pack`, which can rewrite many place files. The design relies on `data-sync` to resolve the conflicts.
5. **The same rule is written in several places.** Statuses (`lib/photo_registry.py PERMANENT` and the schema; #877). Retry windows (180 days in `photo_registry`, 90 in each job; `fixcoords` writes `expiresAt = now + 1 s` to get past the validator). Picture to larger copy (`validate_data.py`, `photos.prune_large`, `largeplacephotos`, `droppictures` for species, `pages_payload`). Story length (`validate.py` in characters; `gemini_stories.py` copies the numbers and adds words; `story_batch.py` and `gemini_stories.py` each define `words()`). Wrong pictures are kept in a list inside `fixcoords.WRONG_PICTURES`.
6. **CI hides failures.** `validate.py ... | tee` then `! grep -q ERROR` has no `pipefail`: if `validate.py` crashes without printing "ERROR" the step is green. 20 data workflows pipe through `tee` the same way; three were fixed one at a time (#770, #869, #881). Five job test files are not run by CI (`commonsphotos`, `droppictures`, `gbifphotos`, `licences`, `largephotos` were re-checked; the review lists 11 in all) because `ci.yml` lists test files by hand, while `tests/data` uses a glob. `droppictures` is one of the jobs that remove place pictures.
7. **Writers learn the rules from a red pull request.** The writer does not know the final validator's rules: two thin story drafts failed a batch (#885), a stale larger copy failed the daily photo batch (#880), a skipped ancestor skipped the judge silently (#882).
8. **Matching by name.** The category pass matches a Commons category by name. Its fourth run (15 Nov, #890 and #892) was wrong twice in four: a category named just "Crawford State Park" or "Shell Mound Park" carries no state, so the job takes the Washington or Florida park for the Kansas or Alabama one. A guard on file names (#891) only moved the failure.
9. **Inputs outside CI.** Story research and drafts live on the `research` and `gemini-stories` branches. `data/geo/geo.json` was generated once outside the repository and has no rebuild path.
10. **Freshness and completeness are not measured.** `build/data_quality.py` prints four indicators, two of them wrong, with no thresholds and no age.

## What went wrong, 12 to 15 Nov, by root cause

| root cause | incidents |
|---|---|
| A. Files and index written separately, many writers, no transaction | #870 and #874 stray larger copy; #876 and #880 Arrowhead copy; #771 and #774 invalid `missing.json`; #806 pictures put back |
| B. A rule written more than once | #877 statuses; #885 story length |
| C. Identity by name or title, not a stable id | Commons category mismatches (#761, #763, #765, #890, #892); wrong Wikipedia page (#842); Harriman and Village Creek collisions; glued names in research (#854) |
| D. Derived data not refreshed when its source changes | food webs after the coordinate fix (#863, #872); outlines and stories still stale |
| E. Bad source data with no check of its meaning | 17 to 23 wrong coordinates (#767, five fix PRs); the "Boiling State Parkrings State Park" name |
| F. CI and workflow failures swallowed | #770 `tee`; #869; #881 browser error instead of the cause; #882 silent skip; #883 skipped steps |

The fixes of this week (#873, #877, #880, #883, #884, #885, #891) each closed the case that failed. They did not remove causes A, C, D or F.

## What the first version got wrong

It listed 13 place-picture writers (about 7 is right); said "no gap found" for outlines, species and diets (there are wrong outlines and 18,000 overrides); proposed a coordinate check "inside its own state", which would pass `nyrobertmoses`; kept the title as the picture's key; and did not see the overlay, the swallowed exit codes, the untested job tests, the shared-title collisions, the cross-PR race or the stale derived data.

## Not covered

Whether a picture's content matches its subject (no image was viewed). Whether GBIF counts, feeding links or taxonomy are right in the real world. Ages older than 12 Nov. Species names and taxonomy beyond the checks above, the research and `gemini-stories` branches beyond the story rules, outline generation, the map style.
