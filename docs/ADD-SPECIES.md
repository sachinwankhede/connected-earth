# Adding a species: one process, complete or not at all (design, 18 Nov 2026)

Part of #1023 (how a place, a species and a journey are created) and a prerequisite of #1061 (one row per concept). Owner requirements, 18 Nov: a species is created in one go with all its data, behind admission rules; no licensed picture from any source means no row, and the refusal is written down; the conservation entry is optional. This document answers: how does it work, is it a workflow or a script, one species or many, and how does it run on GitHub.

Terms: a **row** is one entry of the species table (`data/species/rows/` for species, `data/nodes/rows/` for resource rows); a **node** is one circle in one place's food web and points at a row by `sp`; the **other data files** of a species are its picture files (`photos/species_*.json`), `taxonomy.json`, `about.json` and `conservation.json`, each keyed by the row's id.

## 1. What exists today
The row is made as a side effect of `build/species.py pack()`. The pictures come from `jobs/speciespictures.py` (sources in `lib/species_sources.py`), the taxonomy from `jobs/taxonomy.py` (GBIF), the summary from `jobs/about.py` (first sentences of the Wikipedia page), the conservation status from `jobs/conservation.py` (Wikidata). Each is a separate scheduled or manual job with its own queue, so a new row sits incomplete until all four have caught up (#1054, section 1.2).

## 2. The shape
**A script that composes the existing pieces, run by one workflow.** `jobs/addspecies.py` takes a list of candidates and, for each, runs the steps below in order, cheapest first, stopping at the first refusal. It reuses the code of the four jobs above (their source functions, GBIF lookup, summary fetch, Wikidata query) instead of copying it; those jobs stay for refreshing data that already exists. The row id comes from `lib/species_rows.py` (`ensure`, proposed in #1054).

A candidate is `{wiki title, optional Latin name, kind (taxon or resource), the places and nodes that want it}`.

| Step | Check | On failure |
|---|---|---|
| 1 Identity | The title resolves (redirects followed) to an existing article that is not a disambiguation page and not a redirect to a page a row already has (the row's `wiki` is unique per kind). A row for that page already exists: return its id, create nothing. | Refuse: `no article`, or reuse the existing row. |
| 2 Picture (species and resource) | Every picture source is tried in order (`find_*` of `lib/species_sources.py`); the first accepted picture wins (licences of #421, named author). Taxon rows only: also the large copy. | Refuse: `no licensed picture`. |
| 3 Taxonomy (taxon only) | GBIF backbone match as in `jobs/taxonomy.py`; a doubtful match goes to the review file and counts as missing. | Refuse: `no taxonomy`. |
| 4 Summary | First sentences of the Wikipedia page as in `jobs/about.py`, within the word limit. | Refuse: `no summary`. |
| 5 Conservation (taxon only) | Wikidata status as in `jobs/conservation.py`. | Not an error: no entry, the row is kept. |
| 6 Commit | The row and every file are written together through the existing writers (`SpeciesPhotos`, the taxonomy and summary writers, `NodePhotos` for resources): files first, lists last, as `lib/node_photos.py` already does, so a killed run leaves at worst a file no list mentions. | The whole candidate is dropped. |

A refused candidate gets no row. The node that wanted it keeps the nearest existing row. The refusal goes to a **refusal ledger**: the page, the kind, the places and nodes that wanted it, the sources tried and when, the reason. It is retried after the usual hold (90 days) and whenever a source is added. A count of refusals by page is the priority list for the next picture source. (Where the ledger lives is decided in the first pull request: a new file or the existing missing and tried files with a new status.)

The admission rules (which steps are required, the hold, the word limit) live in `lib/contracts.py`, so tightening or relaxing a rule is one edit with a test.

## 3. One species or many
Both. The unit of work is one candidate, and a run takes a list. Each candidate commits or is refused on its own; one failure never blocks the others. A run has caps like `placepictures`: a time budget (`--minutes`), a limit on pictures' total size (`--max-mb`) and a count (`--limit`). The polite Wikimedia client allows one request every 2 seconds and a species needs roughly 10 to 20 requests, so 75 species is about 30 to 50 minutes.

## 4. How it runs on GitHub
`.github/workflows/data-addspecies.yml` (owner-merged, as all workflows), modelled on `data-placepictures.yml` and `data-fixcoords.yml`:
- **Trigger:** `workflow_dispatch` with inputs `titles` (one per line, or empty to use the queue), `kind`, `dry` (default `yes`), `minutes` and `limit`. Later also called by `data-after-promote` (as it starts `data-placepictures` today) and a weekly schedule that retries due refusals.
- **Steps:** checkout `main`, run `jobs/addspecies.py`, run `build/validate_data.py` and the picture validator, open one data pull request. No secrets: only `GITHUB_TOKEN`; all downloads go through `lib/fetch.py` and the hosts already in `lib/allowed_sources.json`. No paid API.
- **Concurrency:** the group of the photo jobs (`data-photos`), because it writes the same files; one run at a time.
- **The pull request body** lists, per added species, the sources and licences and the author, and the refusals with their reason; the 10-item spot check of `docs/PROMOTION.md` applies. The agent merges on a green `gate` as for any data pull request.
- **A dry run** does every lookup and writes nothing, and prints what would be added and what would be refused (this is how the first run is judged).

## 5. Where requests come from
1. **By hand:** the `titles` input. This is how the first runs go, and how the plan of #1061 (about 75 species and 23 resource rows) is executed.
2. **From the build:** a node whose title has no row becomes a candidate instead of a bare row; `pack()` stops creating rows and fails when a node has no `sp` (the order is in #1054, step 3).
3. **From a place job:** `autogen.py` calls `ensure()` while it builds the web and a missing row becomes a candidate.

## 6. What this does not change
Refreshing existing data stays with the four jobs. The validator gains one rule: a data pull request that adds a row with any required file missing fails.

## 7. Risks
- **Rate limits:** the 2-second gap and a time budget; a throttled source stops the run (as `placepictures`), it is not retried in a loop.
- **A wrong identity** (a title that is a different organism): step 1 refuses disambiguation pages and redirects; GBIF's match confidence in step 3 catches the rest; every addition is in the pull request for the spot check.
- **Picture rule too strict:** the refusal ledger shows it. Relaxing it is a change in `lib/contracts.py`.
- **Two runs adding the same species:** one concurrency group, and `ensure()` returns the existing id.

## 8. Order of work
1. This document read and decided (owner).
2. `lib/species_rows.py` with `ensure()` and the refusal ledger, with tests, nothing calling it.
3. `jobs/addspecies.py` composing the steps, with fakes in tests; `--dry`.
4. `data-addspecies.yml` (owner-merged); a dry run with a few titles; then a live run with the resource rows of #1061.
5. The validator rule; `pack()` stops creating rows (per #1054).

## 9. Owner decisions needed
- Is the summary required (this document says yes)? Is the conservation entry optional (yes, owner)?
- Are the steps' order and "stop at the first refusal" right, or should a run record every failing step for the ledger?
- One refusal ledger for species and resource rows, or one each?
- Does the weekly retry run on a schedule (a `.github/**` change) or by hand until it is trusted?
