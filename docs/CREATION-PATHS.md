# How a place, a species and a journey are created (map and proposal, 17 Nov 2026)

Part of #1023 and #887. Written proposal only, no code. Owner go-ahead 17 Nov. Read with `docs/DATA-PLAN.md` (principles 1 to 6) and `docs/ARCHITECTURE-DATA.md`. Everything below was read in the code on main at `925de2e`; claims not checked in code are marked **unverified**.

## 1. The map today

### 1.1 Place

**Who creates one.** Only `build/state.py` (run by `data-state` for one state, `data-states` for several) creates a place file. `jobs/worldparks.py` (`data-worldparks`) writes only a candidate list ("no place files are made here"); no job turns that list into places, so non-US places and the original national parks came from earlier one-off runs that are not in the repo (**unverified**: no script or workflow for them was found). `jobs/regenplaces.py` and `jobs/regen.py` rebuild the food web of an existing place and keep the rest.

**The steps, in order** (`build/state.py`, `__main__`):

1. `seed()` reads PAD-US, drops golf clubs and refuges, takes the largest `top + 6`, picks points with `jobs/points.py`, and removes near-duplicates inside the state with `jobs/dupes.py`.
2. `jobs/draft.py` (GBIF species and GloBI links) writes `drafts/<id>.json`.
3. `jobs/autogen.py` writes `out/<id>.json` (the place in the app schema). `jobs/names.py --from-data` fills `jobs/names.json` ({Latin name: common name}); `autogen.py` runs again so the nodes carry common names.
4. The result is copied to `data/places/<id>.json` with `stage: pilot`, unless a non-pilot file of that id exists. A new file in `data/order/` lists the ids.
5. `jobs/wikinames.py <ST>` rewrites `name`, `short` and the Wikipedia source from the matched article.
6. `build/species.py pack` turns node Latin names into species ids (`sp`) and creates missing species rows (see 1.2), then `place_inputs.stamp` records the food web.
7. `jobs/bounds.py` writes the outline. Photos, outline top-ups, about lines and stories come later from `placepictures`, `data-outlines`, `data-about` and the story pipeline; promotion (`data-promote`, `build/promote.py`) only drops `stage`.

**The id.**

| id | derived where | from what |
|---|---|---|
| place id | `build/state.py` `slug()` and `seed()` (`i = st.lower() + slug(n)`) | the PAD-US unit name with its type suffix removed, lowercased, non-letters dropped, cut to 16 characters |
| node id (inside one place) | `jobs/autogen.py`, the `ids` loop near line 128 | the **common name** with non-letters dropped, cut to 14, `2`, `3` added on a clash inside that place |
| species id `sp` on a node | `build/species.py` `pack()` then `assign()` | matched by lowercase **Latin name** (`key`); `sid = slug(latin)`, `-2` on a clash, then frozen in the row |

**What touches a place afterwards.** `jobs/wikinames.py` (name), `jobs/fixcoords.py` and `jobs/fixoutlinepoints.py` (point), `lib/place_photos.py` (picture), `jobs/bounds.py`, `bounds_more.py`, `dropoutlines.py`, `stampoutlines.py` (outline), `lib/place_inputs.py` (web and story records), `jobs/gemini_stories.py`, `promote_stories.py`, `story_batch.py` (story), `jobs/about.py`, `jobs/cleanoverrides.py`, `jobs/droppictures.py`, `jobs/syncmain.py` (merges place files key by key). Validators: `build/validate.py` (per file), `build/validate_data.py` (the id set comes from file names in `place_ids()`, order file, outline has a place, name and wiki override limits, point inside outline), `build/promote_check.py` (at promotion only).

**Where it can disagree or duplicate.**

- The place id is a name, not an identity. Two units whose names reduce to the same 16 characters in one state get one id; `state.py` skips an existing non-pilot file silently (`continue`) and overwrites an existing pilot file. Nothing reports the clash.
- No check across states or across the whole set for the same park under two ids. `dupes.py` works only inside one run's list. `sdponca` and `neponca` (`docs/DATA-PLAN.md`, lesson 6) is the case that got through. `worldparks.py` marks "have" by Wikipedia title, name or 5 km, but only for its own report.
- `validate_data.place_ids()` takes the id from the **file name**. Today every file's `id` equals its name (1,548 of 1,548, checked with a script), but the validator does not require it.
- Step order matters and is not checked: a run killed after step 4 and before step 6 leaves nodes with a Latin name and no `sp`; `species.join` raises only when the build runs. `data-state` runs `pack`, `build` and `validate.py` before it opens the pull request, so the failure shows there, but the data is already written.
- `build/state.py` has no test (no `state` file in `tests/jobs/`; `autogen`, `draft` and `names` have none either).

### 1.2 Species

**Who creates one.** Exactly one code path creates a species row: `build/species.py pack()`. It runs in `data-state`, `data-states`, `data-promote`, `data-regen`, `data-regenplaces`, `data-names`, `data-outlines`, `data-about`, `data-diets`, `jobs/fetch_all.sh`, `jobs/syncstep.sh` and `ci.yml`. It reads every place's full nodes, votes on the shared fields (`SHARED`), and for any lowercase Latin name (or name when there is no Latin) with no existing row writes `data/species/rows/<xx>/<sid>.json` (`data/nodes/rows/` for a resource), marked `src` (from `SPECIES_SRC`, default `manual`) and `at`. An existing row is never rewritten by the vote.

**The id.** `species.assign()`: `slug(latin)` (name when no Latin), `-N` on a clash, stored once and frozen. `sk` (taxon, group, resource) comes from `kind_of()`, a regex on the name (`GROUP`) or the presence of `cat`. Today there are 5,072 rows, no repeated lowercase Latin name and no `-N` suffix.

**Sidecars and later writers.** `lib/species_photos.py` with `jobs/speciespictures.py` (picture, credit, missing, tried; all by sid), `jobs/taxonomy.py` (`taxonomy.json`, `taxonomy_review.json`, by sid), `jobs/conservation.py` (`conservation.json`, `conservation_asked.json`; by sid since #1024), `jobs/about.py` and `species.py about` (the `about` line on the row), `jobs/diets_resolve.py` and `build/diets.py` (`data/diets/<xx>/<sid>.json`), `jobs/dropunnamed.py`, `jobs/cleanauthors.py`. `data/species/order_names.json` is still keyed by name (`build/build.py` line 455). `jobs/names.json` is keyed by Latin name and feeds `autogen.py`.

**Validators.** `validate_data.check()` (row shape, file sits at the path its sid says, sidecars keyed by existing sids, override limits, photo lists by sid), `lib/species_photos.check()`, and the read-only `build/stale_report.py` and `build/data_status.py`.

**Where it can disagree or duplicate.**

- Identity is decided by a name at the last moment. A node arrives with a Latin string from `autogen.py` (the GBIF name) and `pack()` matches it by string. A synonym, a subspecies, other capitalisation or a typo makes a **second row** for the same organism with a second sid, and nothing compares rows beyond exact lowercase equality (`by_name`). I checked exact and punctuation-stripped duplicates (none today); I did not check synonyms (that needs the GBIF backbone).
- `pack()` rewrites every place file as a side effect of a job about something else, and in one call creates rows, slims nodes, stamps food-web records and moves diet evidence, with no transaction (the last line of `docs/DATA-PLAN.md` already says "no silent rewrite").
- The common name a node shows is chosen before the row exists (`autogen.py`: `NAMES`, `npscommon`, GBIF `common`, `names.py`), so the first place to create a species decides its name and `wiki`; later places can only override. The override limits (972 names, 1,066 wikis in `validate_data.py`) exist because of this.
- A new row has no taxonomy, picture, conservation entry or `about`. Each arrives from a different job later. A species missing from a sidecar shows only in `data_status.py` counts; the validators check sidecars for orphans, not completeness (by design, rule 10).
- `name_key()` falls back to `name` when `latin` is empty, so a non-organism row and an organism with an empty Latin field could collide.

### 1.3 Journey

**Who creates one.** No job writes a journey. `jobs/journeys.py` (`data-journeys`) ranks candidate species into `research/journey-candidates.md`; `jobs/journeyresearch.py` (`data-journeyresearch`) gathers source text into `research/journey-research.md`; a person or agent then writes `data/journeys/<id>.json` by hand (`docs/PROMOTION.md`, "Finding more journeys"). There are 19 journey files plus `config.json`. `lib/journey_photos.py`, `jobs/journeypictures.py` and `jobs/rekeyjourneyphotos.py` write the cover picture by journey id after the journey exists.

**The id.** The `id` field inside the file, typed by the author. `build/journeydata.py` loads the files; `validate_data.check()` requires a non-empty id not repeated across journeys. It does not require the id to equal the file name (I opened one file: they match; **unverified** for the rest).

**What a journey refers to.** Places by `ends[].eco` (a place id; checked to have a file and not to be `level: local`) and, in `ends[].node`, a node id inside that place. The species is named only by `imgwiki` (a Wikipedia title, such as "Chilean flamingo") and free text. In `validate_data.py` lines 143 to 152 only `eco` is checked; I found no check that `node` exists in the place's nodes or that its species matches `imgwiki` (**unverified**: `validate.py` or the build may check it).

**Where it can disagree.**

- A journey has no species id. The link between journey, species row and place nodes is three unrelated strings (`imgwiki`, `ends[].node`, free text). Renaming a node or merging two species rows would break a journey silently.
- `jobs/journeys.py` ranks by Latin name from the place files, not by sid.
- `pos` is typed per file; a duplicate or gap is not reported by what I read (**unverified**).
- Journey pictures are already by journey id, so the creation path is the odd one out.

### 1.4 Where the three differ without a reason

| | place | species | journey |
|---|---|---|---|
| created by | `build/state.py` (job chain) | `species.pack()` as a side effect | by hand |
| id assigned | from a name in `seed()` | from the Latin name in `pack()`, then frozen | typed |
| id assigned at | the start | the end of the chain | the start |
| id checked for uniqueness against | a file of that name only | the exact Latin string only | other journeys only |
| first complete check | `data-state` runs `validate.py` and budget | CI `validate_data` | CI `validate_data` |
| tests of the creation code | none | **unverified** (`pack` is exercised through other tests) | none |

The same shape three times: id from a name, side-effect writes, checks later and elsewhere.

## 2. Proposal

**One rule.** An id is assigned once, at creation, by one function, and nothing after that matches by name. A name is an input to creation and an attribute afterwards. This is DATA-PLAN principles 1, 2 and 6 applied to creation.

### 2.1 One module per kind in `lib/`, each with `check()`

Modelled on `PlacePhotos`, `SpeciesPhotos` and `JourneyPhotos` (files first, lists last, `os.replace`, `check()` finds any disagreement):

- `lib/places.py` (`Places`): `create(candidate)` returns the new id or a reason it refused; `check()`.
- `lib/species_rows.py` (`SpeciesRows`): `ensure(latin, name, source)` returns the sid, creating the row if none exists; `check()`.
- `lib/journeys.py` (`Journeys`): `create(draft)`; `check()`.

Each `create` is idempotent: asking twice gives the same id and one record.

**Place.** `create` takes the PAD-US (or Wikidata) unit and computes the id once. The id stays `<state><slug>` so no existing id changes, but it first looks the candidate up across **all** places, not only the run: same Wikipedia title, same name within 8 km, or a point within 5 km sharing a distinctive word (the `dupes.py` and `worldparks` rules, moved to one place). A hit is a refusal listed in the report, never an overwrite and never a silent skip. A slug that collides with a different place gets a numbered id and the pair is reported. The sidecar records are created with the file: `place_inputs` (web, story), the photo missing state, the outline record. A new place is whole from its first commit.

**Species.** Every node is created with its sid, not a Latin string. `autogen.py` (or its replacement) calls `SpeciesRows.ensure(latin)` while it builds the web. `ensure` matches in one order: GBIF key (from `taxonomy.json` or the draft's `speciesKey`), then accepted Latin name, then synonym through the GBIF match `jobs/taxonomy.py` already uses, and only then creates a row. It writes the row and its empty sidecar records (taxonomy review, species missing, conservation asked) together. `pack()` stops creating rows and stops matching by name; it keeps slimming nodes. Rows gain the GBIF `key`, which makes the duplicate check exact and feeds `taxonomy.py`.

**Journey.** `Journeys.create` takes a draft with the species as a **sid** and each end as `(place id, node id)`, reads the species row for `imgwiki` and the name, refuses an end whose node does not exist or whose node's `sp` is not that sid, assigns `pos`, and writes the file and the `JourneyPhotos` slot. `check()` adds `ends[].node` exists, species matches, `id` equals the file name, and `pos` is unique.

### 2.2 Minimal step list

Small pull requests, built output unchanged where possible (compare `index.html` and `api/` before and after, as in #1013).

1. **Read-only audit** (`build/creation_report.py`): across all places, same-park candidates (name, title, distance); species rows sharing a GBIF key or a synonym; journeys with an end node that is missing or whose species differs from `imgwiki`; id versus file name for places and journeys. No behaviour change; its numbers decide whether steps 3 to 5 are needed at all. Agent merges.
2. **Validator additions** for what the audit finds already clean (place `id` equals file name, journey `id` equals file name, `ends[].node` exists and has the right species). Agent merges once the data passes.
3. **`lib/species_rows.py` with tests**, nothing calling it; then `autogen.py` calls `ensure` and writes `sp`, and `pack()` stops creating rows (it fails when a node has no `sp`). `jobs/names.py` stays the common-name source, read through `ensure`. Output unchanged for existing data. Agent merges.
4. **`lib/places.py` with tests**, after an offline fixture run of `state.py` exists (it has no test today); then `state.py` calls it (whole-set duplicate refusal, id clash report, records created with the file). The validator gains a whole-set duplicate-park check. Agent merges.
5. **`lib/journeys.py`** and a manual `data-journey-new` workflow (owner-merged, `.github/**`). The 19 files get an `sp` field from a one-off job; the app and build keep reading `imgwiki` until the check proves it matches.
6. **Retire** the items below after one good run of the new path.

### 2.3 What the new path makes unnecessary (owner to confirm; I did not check that nothing else calls them)

- `species.pack()` as a creator of rows and its `name_key` and `by_name` matching (the function stays for slimming). The `species.py pack` calls in `data-names`, `data-outlines`, `data-about`, `data-diets` and `data-regen*` could be dropped where the job does not touch nodes.
- `jobs/names.json` keyed by Latin name, once `ensure` stores the common name on the row (`jobs/names.py` stays as a lookup helper).
- `jobs/dupes.py` (moves into `lib/places.py`).
- The node id built from the common name in `autogen.py` (`base[:14]`). Replacing it touches every place file, `raw`, `ev`, `tip`, journeys and the layout, so it is **not** in the first pass (see risks).
- `data/species/order_names.json` stays name-keyed unless the owner wants it moved (it holds order names, not species; **unverified** that nothing needs its keys to be sids). `conservation.json` is already by sid (#1024), which closes that question in #1023.
- `jobs/worldparks.py` stays (it is a list). The missing creation step for non-US places would be a second input to `Places.create`, not a new job.
- Workflows that change (all `.github/**`, owner-merged): `data-state`, `data-states` (call the new module), `data-names` (only if `wikinames` folds into `create`), and the trimmed `pack` calls.

### 2.4 Risks

- **Re-keying nodes is the large step.** A node id is used by `raw`, `ev`, `tip`, journeys' `ends[].node`, layout (`xh`) and the app. Leaving node ids alone keeps the built output identical.
- **Synonym matching can merge two real species.** It sits behind GBIF's accepted key and reports a merge instead of doing one; a wrong merge is worse than a duplicate row. Start with exact key and name, add synonyms only after the audit shows how many there are.
- **A duplicate-park refusal can hide a real second park** (two parks 3 km apart with similar names). Refusals list their reason, and a person overrides with an explicit flag.
- **`state.py` has no tests**, so step 4 needs the offline fixture run first or the change cannot be proved.
- **Merge clashes:** `syncmain.py` merges place files key by key; each new per-place record file needs its rule there or two branches will clash.
- **Size and speed:** extra sidecars add files, not bytes in the first view; budgets still apply.

### 2.5 Owner decisions needed

1. Approve the direction: one creation function per kind, id assigned at creation, no name match afterwards.
2. Whether node ids inside a place stay as they are (recommended for now).
3. Whether synonym matching is in scope or only exact key and name for now.
4. The workflow changes (`.github/**`, owner-merged): `data-state`, `data-states`, a new `data-journey-new`, and trimming `species.py pack` calls.
5. The retirement list in 2.3.
6. Whether #1016 (regions by id) stays separate (recommended: it is a fourth kind; fold it in when its own map is done).
