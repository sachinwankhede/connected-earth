# Adding a species: the one standing process, complete or not at all (design, 18 Nov 2026)

Part of #1023 (how a place, a species and a journey are created). **This is the standing process for every species that will ever be added to the project**, whatever starts it: a new place whose food web names an organism we have no row for, a promotion, a manual request, or a cleanup. The one-off cleanup of #1061 (one row per concept, about 75 species rows and 23 resource rows) is only the first use and is described in the last section; nothing in the process is specific to it.

Owner requirements, 18 Nov: a species is created in one go with all its data, behind admission rules; no licensed picture from any source means no row, and the refusal is written down; the conservation entry is optional. This document answers: how does it work, is it a workflow or a script, one species or many, and how does it run on GitHub.

Terms: a **row** is one entry of the species table (`data/species/rows/` for species, `data/nodes/rows/` for resource rows); a **node** is one circle in one place's food web and points at a row by `sp`; the **other data files** of a species are its picture files (`photos/species_*.json`), `taxonomy.json`, `about.json` and `conservation.json`, each keyed by the row's id.

## 1. What exists today
The row is made as a side effect of `build/species.py pack()`. The pictures come from `jobs/speciespictures.py` (sources in `lib/species_sources.py`), the taxonomy from `jobs/taxonomy.py` (GBIF), the summary from `jobs/about.py` (first sentences of the Wikipedia page), the conservation status from `jobs/conservation.py` (Wikidata). Each is a separate scheduled or manual job with its own queue, so a new row sits incomplete until all four have caught up (#1054, section 1.2).

## 2. The shape
**A script that composes the existing pieces, run by one workflow.** `jobs/addspecies.py` takes a list of candidates and, for each, runs the steps below in order. If identity fails it stops (there is nothing to look up); otherwise it runs every remaining step and records the result of each (found, missing, or skipped), so the ledger shows everything that is missing and not only the first thing. The row is added only when every required step passed. It reuses the code of the four jobs above (their source functions, GBIF lookup, summary fetch, Wikidata query) instead of copying it; those jobs stay for refreshing data that already exists. The row id comes from `lib/species_rows.py` (`ensure`, proposed in #1054).

A candidate is `{wiki title, kind (taxon or resource), optional Latin name}`. It carries nothing about places: a species exists on its own, with or without a place that uses it.

| Step | Check | On failure |
|---|---|---|
| 1 Identity | The title resolves (redirects followed) to an existing article that is not a disambiguation page and not a redirect to a page a row already has (the row's `wiki` is unique per kind). A row for that page already exists: return its id, create nothing. | Refuse: `no article`, or reuse the existing row. |
| 2 Picture (species and resource) | Every picture source is tried in order (`find_*` of `lib/species_sources.py`); the first accepted picture wins (licences of #421, named author). Taxon rows only: also the large copy. | Refuse: `no licensed picture`. |
| 3 Taxonomy (taxon only) | GBIF backbone match as in `jobs/taxonomy.py`; a doubtful match goes to the review file and counts as missing. | Refuse: `no taxonomy`. |
| 4 Summary | First sentences of the Wikipedia page as in `jobs/about.py`, within the word limit. | Refuse: `no summary`. |
| 5 Conservation (taxon only) | Wikidata status as in `jobs/conservation.py`. | Not an error: no entry, the row is kept. |
| 6 Commit | The row and every file are written together through the existing writers (`SpeciesPhotos`, the taxonomy and summary writers, `NodePhotos` for resources): files first, lists last, as `lib/node_photos.py` already does, so a killed run leaves at worst a file no list mentions. | The whole candidate is dropped. |

A refused candidate gets no row. The refusal goes to a **refusal ledger**: the page, the kind, the result of each step, when it was tried and the reason (nothing about places). It is retried after the usual hold (90 days) and whenever a source is added. A count of refusals by page is the priority list for the next picture source. (Where the ledger lives is decided in the first pull request: a new file or the existing missing and tried files with a new status.)

The admission rules (which steps are required, the hold, the word limit) live in `lib/contracts.py`, so tightening or relaxing a rule is one edit with a test.

## 2.1 The model, and the input
**The dependency runs one way: a place needs a species, never the reverse.** A species is complete without any place. A place can create a node only for a species that is already available (it has a row with all its data). So the species process knows nothing about places, nodes or who asked; it takes a title and either adds the species or refuses and records why.

One candidate is `{title (the Wikipedia article), kind (taxon or resource), optional Latin name}`. A run gets its candidates from three places:
1. **A list typed into the workflow** (`titles`), for a species someone wants added now.
2. **A caller on the place side.** When the place process needs a species it asks the species registry for it (`ensure(title)`); if the species is not yet there, the place process asks this process to add it first. If the species is refused, the place side decides what its node does (use the nearest available species, or leave the node out); that choice belongs to the place process, not to this one.
3. **The refusal ledger:** refused candidates whose hold has expired (the weekly retry, below).

A **gap report** on the place side (`build/` script, read-only) lists the species titles that existing nodes name and no row has; it is how a backlog such as the cleanup of #1061 is turned into a list for input 1. It is a report about places, not an input of the species process.

The place and journey processes use the same frame (a candidate, ordered steps with a recorded result each, an all-or-nothing commit, a ledger). They depend on species the way described above: a journey needs its species by id, a place needs the species of each node.

## 3. One species or many
Both. The unit of work is one candidate, and a run takes a list. Each candidate commits or is refused on its own; one failure never blocks the others. A run has caps like `placepictures`: a time budget (`--minutes`), a limit on pictures' total size (`--max-mb`) and a count (`--limit`). The polite Wikimedia client allows one request every 2 seconds and a species needs roughly 10 to 20 requests, so a batch of 75 species is about 30 to 50 minutes (the largest batch we expect, the cleanup below).

## 4. How it runs on GitHub
`.github/workflows/data-addspecies.yml` (owner-merged, as all workflows), modelled on `data-placepictures.yml` and `data-fixcoords.yml`:
- **Trigger:** `workflow_dispatch` with inputs `titles` (one per line, or empty to use the queue), `kind`, `dry` (default `yes`), `minutes` and `limit`. Later also called by `data-after-promote` (as it starts `data-placepictures` today) and a weekly schedule that retries due refusals.
- **Steps:** checkout `main`, run `jobs/addspecies.py`, run `build/validate_data.py` and the picture validator, open one data pull request. No secrets: only `GITHUB_TOKEN`; all downloads go through `lib/fetch.py` and the hosts already in `lib/allowed_sources.json`. No paid API.
- **Concurrency:** the group of the photo jobs (`data-photos`), because it writes the same files; one run at a time.
- **The pull request body** lists, per added species, the sources and licences and the author, and the refusals with their reason; the 10-item spot check of `docs/PROMOTION.md` applies. The agent merges on a green `gate` as for any data pull request.
- **A dry run** does every lookup and writes nothing, and prints what would be added and what would be refused (this is how the first run is judged).

## 5. Where requests come from (every entry point uses the same steps)
1. **By hand:** the `titles` input, for any species the owner or the agent wants added.
2. **From the place side:** a node whose title has no row no longer gets a bare row: `pack()` stops creating rows and fails when a node has no `sp` (#1054, step 3); `autogen.py` asks for the species by title while it builds the web, as in section 2.1.

## 6. What this does not change
Refreshing existing data stays with the four jobs. The validator gains one rule: a data pull request that adds a row with any required file missing fails.

## 6.1 Integrity and duplicates
**How a duplicate is avoided: identity is decided before anything is written, in a fixed order, and a doubt is reported, never merged.** Step 1 looks the candidate up against the existing rows in this order, and stops at the first hit:
1. **The same Wikipedia article** (after redirects) as an existing row of the same kind: return that row's id, create nothing. A row maps to one unique page.
2. **The same GBIF accepted key** (taxon rows): two titles that GBIF says are one species (a synonym, an old name) are one row. This is what catches the duplicates a redirect does not.
3. **The same Latin name or the same row id** (`slug(latin)`; the name when there is no Latin): never a second row with the id of an existing one.
4. **Not found:** a new row. If two of these tests disagree (the page is a row's, the GBIF key is another row's), the candidate is refused with `conflict` and both rows named in the ledger, and a person decides; synonym matching never merges two rows on its own (#1054 section 2.4).

**What the validator enforces from the first run.** For rows added by this process, errors in `build/validate_data.py`: one row per `wiki` per kind, one row per GBIF key, one row per id, and every required file present for the row. The rows that already break these (the 56 shared pages of resource rows, the taxon pairs; see `build/species_report.py`) are held by a count limit that may only go down, as the override limits are, until the #1061 cleanup removes them.

**Other guards.** Each candidate commits all or nothing (files first, lists last, as `lib/node_photos.py` does), so a killed run leaves no half-made species; `ensure()` is idempotent, so a repeated or retried run returns the same id; all runs share one concurrency group, so two runs never add at once; and the validators run on the finished tree before a pull request opens. What is not covered: two data pull requests open at the same time that add the same species. The second one conflicts on the row file and is resolved by hand (or refused by the validator once the first has merged).

## 6.2 Schema and model
**What is checked today.** `build/schemas/<kind>.schema.json` is the written contract of a file, checked in `build/validate_data.py` through `shape()`. The species row (`species-row`), `taxonomy`, `taxonomy-review`, `about` and the picture miss records (`photo-missing`) have one. `tests/data/writer_schema_test.py` fails when a schema has no entry in its `WRITERS` list and, for a record made by a `lib/` writer, validates the writer's real output against the schema; `build/ci_changes.py` runs the data checks whenever `lib/*` or `build/schemas/*` changes (#1055). Not covered today by a schema: the picture credit records (`photos/species_pictures.json`, `photos/node_pictures.json`), `conservation.json`, and the new refusal ledger.

**What this process adds, so that what it writes is correct by construction.**
1. **A schema for every file it writes.** New schemas: picture credit record (species and node), conservation entry and refusal ledger. The row and taxonomy schemas stay.
2. **A real-writer test for each.** `ensure()` (the new row), the ledger writer and the credit-record writers each get a callable sample in `WRITERS`, validated against their schema, so a change to a writer or a schema that does not match fails in CI.
3. **Shape check on the whole tree before a pull request opens.** The workflow runs `build/validate_data.py` on the finished files, as `data-placepictures` does today, and the run fails instead of opening a pull request when a record is wrong.
4. **Model rules, beyond shape.** A row is in the folder of its kind (resource rows only in `data/nodes/rows/`; the validator already checks this); a resource row has a `cat` of abiotic or decomp, a taxon row a Latin name, a taxonomy entry and a species picture; every sidecar entry is keyed by an existing row id; every node's `sp` is an existing row. These are in `build/validate_data.py`, with the uniqueness rules of section 6.1.
5. **One place for the rules.** Required steps per kind, the hold and the word limit live in `lib/contracts.py`; the validator reads them from there, so the process and the check cannot drift apart.

## 7. Risks
- **Rate limits:** the 2-second gap and a time budget; a throttled source stops the run (as `placepictures`), it is not retried in a loop.
- **A wrong identity** (a title that is a different organism): step 1 refuses disambiguation pages and redirects; GBIF's match confidence in step 3 catches the rest; every addition is in the pull request for the spot check.
- **Picture rule too strict:** the refusal ledger shows it. Relaxing it is a change in `lib/contracts.py`.
- **Two runs adding the same species:** one concurrency group, and `ensure()` returns the existing id.

## 8. Order of work
1. This document read and decided (owner).
2. `lib/species_rows.py` with `ensure()` and the refusal ledger, with tests, nothing calling it.
3. `jobs/addspecies.py` composing the steps, with fakes in tests; `--dry`.
4. `data-addspecies.yml` (owner-merged); a dry run with a few titles; then the first live use, the cleanup of #1061 (last section).
5. The validator rule; `pack()` stops creating rows (per #1054).

## 9. Decisions (owner, 18 Nov) and the open ones
- **Summary is required.** Decided.
- **Record every step.** Decided; see section 2: identity failing stops the candidate, every other step is run and recorded.
- **Refusal ledger: one writer and one record shape for all kinds, one file per kind** (`species` for taxon and resource rows, later `place` and `journey`). Recommended, not yet decided: the places and journeys will refuse for their own reasons, so a shared shape (`{key, kind, steps: {name: found|missing|skipped, detail}, tried at, hold until}`) lets one library and one report serve all three, while one file per kind keeps data pull requests from clashing (the repository already works this way).
- **Weekly retry.** A scheduled workflow (a `.github/**` change, owner-merged) that every week takes the ledger entries whose hold has expired (90 days) and runs them through the process again, so a picture that has since appeared on Commons or Openverse is picked up without anyone asking. A new picture source also makes every picture refusal due. Recommended: run it by hand until the process has had a few runs, then schedule it.

## 10. The first use: the #1061 cleanup
Not part of the process; one batch that goes through it. The gap report lists, for each node that has its own name or Wikipedia page, whether its page already has a row (the node points at it), is a separate article (a title to feed this process), or has no article (the node uses the nearest row; that is a place-side choice). The candidates are about 75 species and 23 resource rows; the process admits those with a licensed picture, taxonomy and summary, and refuses and records the rest, which then keep the nearest row. Everything learned there (which pictures are missing, which sources are worth adding) goes to the refusal ledger, which is how the same process serves later additions.

## 11. Keeping it general
- The steps, the rules and the ledger do not mention a place, a state or the cleanup; a candidate carries only a title, a kind and the nodes that want it.
- A new kind of row (a group, say) is a new entry in the rules (`lib/contracts.py`: which steps it needs), not new code.
- A new picture source is one function in `lib/species_sources.py`; the refusal ledger tells which source would help most.
- Every change to the rules is a pull request with the number of species it would have admitted or refused in the last run, so a change in admission is visible.

## 12. The interface: one REST-like contract for species, place and journey (design, 22 Nov 2026)
Owner question, 22 Nov: can add species, place and journey have a REST-API-like shape? Yes. The shape below is the same for all three kinds (`docs/ADD-PLACE.md` and `docs/ADD-JOURNEY.md` section 11 refer here). **The transport is not HTTP by default**: the project is a static site with data in git, so the "endpoint" is a GitHub workflow; an HTTP front (section 12.3) is optional and an owner decision.

### 12.1 The contract
| Call | Meaning |
|---|---|
| `POST /species`, `POST /places`, `POST /journeys` | Add one candidate. Body: the candidate of that kind (the JSON each doc defines) and `dry` (default true). |
| `GET /species/{id}` (same for places, journeys) | Read one record and, for a species, the state of its other data files. |
| `GET /ledger/{kind}` | The refusals of that kind: key, steps, tried at, hold until. |

One response shape for every kind:
```
{ "kind": "species|place|journey",
  "status": "added | exists | refused",
  "id": "<id when added or existing>",
  "dry": true,
  "steps": { "<step>": {"result": "found|missing|skipped", "detail": "..."} },
  "reason": "<set only when refused: the first required step that failed, or conflict>" }
```
Rules: **idempotent** (the same candidate twice returns `exists` and the same id, never a second record); **a dry call writes nothing** and returns what would happen; **every step is reported**, not only the first failure; `conflict` names both records. The response has a schema in `build/schemas/` and a real-writer test, like every other file we write.

### 12.2 How it is built
1. **The real API is a function**: `add(kind, candidate, dry) -> Result` in `lib/`, one implementation per kind behind it (`species_rows`, `places`, `journeys`). The validator, the ledger and the workflows all use this one interface.
2. **A command line over it**: JSON in, JSON out (`python3 -m lib.add species '<json>'`). The three workflows call it; `workflow_dispatch` with the candidate as input is the "POST", and the result is the pull request body and a JSON artifact.
3. **Nothing else changes**: the steps, rules and ledger of each document stay as written.

### 12.3 Optional HTTP front: a Cloudflare Worker
A Worker is a small script that runs on Cloudflare's edge, next to the site. It would be a doorway, not the process: it checks a caller's token, validates the body against the request schema, then asks GitHub to run the workflow (`workflow_dispatch`) and returns a run id; the caller polls `GET` for the result, which is read from the pull request or the artifact. It does no adding itself. It needs a secret (a GitHub token allowed to dispatch workflows), a hosted piece the repository does not have today, and a rate limit, so it touches ground rule 4 (secrets and cost) and `.github/**` (owner-merged). Not built before the three processes work; it is only worth building if a caller outside GitHub needs it. Because the contract above already exists, the Worker would be a thin layer over it.

### 12.4 Update: the same steps on an existing record (design, 22 Nov 2026)
Owner question, 22 Nov: should there be a generic update, not one per attribute? Yes. An update is **the add steps run again on the record as it would be after the change**, so add and update use one set of rules and cannot disagree. (Needed first by the cleanup of `docs/NODE-IDENTITY.md`, where a node's species is changed in a place's food web.)

| Call | Meaning |
|---|---|
| `PATCH /species/{id}`, `/places/{id}`, `/journeys/{id}` | Change fields of one record. Body: `set` (field to new value) and `dry` (default true). |

The response is the shape of 12.1 plus `before` and `after` for each changed field. Rules:
- **Same checks as add.** The candidate is the record with the patch applied; identity, model and contract steps run on the whole record, every step is reported, and a failing required step refuses the whole update. A refusal is recorded in the same ledger.
- **Identity fields are not patchable.** `id`, kind, and the page of a row (`wiki`) change only through a rename or merge call, which is a separate operation with its own reference handling.
- **A reference check before any write.** A reverse index lists who points at the record (nodes by `sp`, journey stops, diet and link records). An update that would leave a reference invalid is refused with `references` and the list. Merging two rows is the same check run for every node that names the row.
- **All or nothing, files first.** An update that touches several files (a node in a place file, the journey that names it) commits them together, then the lists; a dry call writes nothing.
- **Data is changed only through this call** (ground rule 1): no hand edit of data and no one-off script that writes data files; a job calls `update(kind, id, patch, dry)` in `lib/` beside `add`, and a workflow (owner-merged) runs a list of patches the same way `data-addspecies` runs candidates.
- **No attribute-specific code.** Which fields a kind has, which are required and what each check is live in `lib/contracts.json`; a new attribute is a new entry there.

Not built. Order: the audit of `docs/NODE-IDENTITY.md` first, then the place update (a node's `sp`), then the others as a need appears.
