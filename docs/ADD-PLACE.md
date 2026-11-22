# Adding a place: the one standing process, whole or not at all (design, 22 Nov 2026)

Part of #1023 (how a place, a species and a journey are created). **This is the standing process for every place that will ever be added**, whatever starts it: a state run, a list of world parks, a manual request. Read with `docs/ADD-SPECIES.md`, which sets the frame this document reuses (a candidate, ordered steps with a recorded result each, an all-or-nothing commit, a refusal ledger, admission rules in `lib/contracts.py`). Facts about today's code come from `docs/CREATION-PATHS.md` (#1054, still unmerged); claims not checked in code are marked **unverified**.

Owner requirements carried over (18 Nov): a place is created in one go with all its data, behind admission rules that can be tightened or relaxed; a refusal is written down; **a place depends on species, a species never on a place**.

Terms: a **place** is one file in `data/places/`; a **node** is one circle in its food web and points at a species row by `sp`; a **candidate** is what a run is asked to add.

## 1. What exists today
Only `build/state.py` creates a place (run by `data-state` and `data-states`). Its steps: `seed()` reads PAD-US and removes near-duplicates inside the state; `jobs/draft.py` and `jobs/autogen.py` build the food web; the file is copied to `data/places/<id>.json` with `stage: pilot`; `jobs/wikinames.py` fixes the name; `build/species.py pack` turns Latin names into `sp` ids and creates missing species rows; `jobs/bounds.py` writes the outline. Pictures, about lines and stories come later from other jobs. `jobs/worldparks.py` only lists candidates; no job turns that list into places (**unverified** for the first national parks).

Where it goes wrong today:
- The place id is a name (the unit name cut to 16 characters), not an identity. `state.py` skips an existing non-pilot file silently and overwrites a pilot one.
- Duplicates are looked for only inside one run's list. The same park under two ids (`sdponca`, `neponca`) got through.
- `validate_data.place_ids()` takes the id from the file name and does not require the `id` field to match.
- Step order is not checked; a killed run leaves nodes with a Latin name and no `sp`.
- A species row is created as a side effect of `pack()`, with no picture, summary or taxonomy.
- `build/state.py` has no test.

## 2. The shape
**A script that composes the existing pieces, run by one workflow**, as for species. `jobs/addplace.py` takes candidates and, for each, runs the steps below in order. Identity failing stops the candidate (nothing is written); every other step is run and its result recorded, so the ledger shows everything that is missing. The place is committed only when every required step passed.

A candidate is `{source (PAD-US unit id, Wikidata id or a Wikipedia title), name, point, state or country, kind of place}`. It carries nothing about species: the food web is built from the species that are available.

| Step | Check | On failure |
|---|---|---|
| 1 Identity | Look the candidate up against **all** existing places (section 3): same Wikipedia article, same name within 8 km, or a point within 5 km that shares a distinctive word. | Refuse: `duplicate of <id>` (or `conflict`, both named). |
| 2 Id | Compute `<state><slug>` once. A clash with a different place gets a numbered id and the pair is reported; never an overwrite and never a silent skip. | Refuse: `id clash` if it cannot be resolved. |
| 3 Position | The point lies inside the place's own state or country and, once the outline exists, inside the outline. | Refuse: `point outside`. |
| 4 Species | Every node's organism resolves to a species row that is available, by id (`ensure(title)` of the species process). A node whose species is refused uses the nearest available species, or is left out; this choice belongs to this process. A web with fewer than the minimum number of nodes is refused. | Refuse: `web too small`. |
| 5 Food web | `jobs/autogen.py` builds the web with `sp` set on every node from the start. `pack()` no longer matches by name. | Refuse: `no web`. |
| 6 Outline | `jobs/bounds.py`. | Refuse: `no outline`. |
| 7 Picture | Place picture sources as in `lib/place_photos.py` (licences of #421, named author). | Refuse: `no licensed picture`. |
| 8 Name and wiki | `jobs/wikinames.py`: name and Wikipedia source from the matched article; a place with no article is refused. | Refuse: `no article`. |
| 9 Commit | The file, the order entry, the outline, the picture and the food-web records are written together; files first, lists last, as `lib/place_photos.py` does. | The whole candidate is dropped. |

Which steps are required is decided in `lib/contracts.py` (for example: is a picture required, or only wanted). The first run can relax picture and article to optional; tightening is one edit with a test.

## 3. Integrity and duplicates
**Identity is decided before anything is written, against the whole set, and a doubt is reported, never merged.** Moves the `dupes.py` and `worldparks.py` rules into one place (`lib/places.py`): same Wikipedia article, same normalised name within 8 km, a point within 5 km with a shared distinctive word. A hit is a refusal naming the other place; a person overrides with an explicit flag (two parks 3 km apart with similar names are possible).

The validator gains, as errors for places added by this process: `id` equals the file name; no two places share a Wikipedia article; no two places are within the duplicate distance with a shared word; every node's `sp` is an existing row. Existing violations are held by a count limit that only goes down, as the override limits are.

Other guards: all-or-nothing commit; `create` is idempotent (asking twice gives the same id and one file); one concurrency group, so two runs never add at once; validators run on the finished tree before a pull request opens. Not covered: two open pull requests adding the same park; the second conflicts and is resolved by hand.

## 4. Schema and model
Every file the process writes has a schema in `build/schemas/` checked through `shape()`, and a real-writer entry in `tests/data/writer_schema_test.py`: the place file, the outline record, the place picture credit and the ledger. The model rules (a node's `sp` exists, a node id is unique inside its place, the point is inside the outline, a place has a name, a wiki source and a state or country) live in `build/validate_data.py` and read their limits from `lib/contracts.py`, so the process and the check cannot drift apart.

## 5. Input, entry points, and GitHub
1. **By hand:** a list in the workflow input (`candidates`).
2. **A state run:** `seed()` produces candidates for a state; each goes through the steps above instead of being written directly.
3. **A world-park list:** `jobs/worldparks.py` output becomes candidates; this is the missing creation path for non-US places.
4. **The refusal ledger:** candidates whose hold has expired (weekly retry; by hand first, then scheduled).

`.github/workflows/data-addplace.yml` (owner-merged) modelled on `data-state`: `workflow_dispatch` with `candidates`, `dry` (default yes), `limit` and `minutes`; `GITHUB_TOKEN` only, downloads through `lib/fetch.py`; one data pull request whose body lists sources, licences, refusals with reasons and the 10-item spot check of `docs/PROMOTION.md`. A dry run does every lookup and writes nothing. `data-state` and `data-states` then call this script instead of `state.py`'s own chain.

## 6. The ledger
Same record shape as species (`{key, steps: {name: found|missing|skipped, detail}, tried at, hold until}`), one writer in `lib/`, **one file for places** so data pull requests do not clash. A count of refusals by step is the priority list for the next source (a picture source, a better article match).

## 7. Risks
- **A duplicate refusal hides a real second park:** the reason is listed and a person can override.
- **Changing how `state.py` works without a test:** an offline fixture run of `state.py` comes first.
- **Node ids stay as they are** (common name cut to 14 characters); re-keying nodes touches journeys, layout and the app and is not part of this.
- **Waiting on species:** the place process needs the species process first; until it exists a node keeps today's behaviour.

## 8. Order of work
1. This document read and decided (owner). The species process (`docs/ADD-SPECIES.md`) comes first because step 4 depends on it.
2. Read-only audit of today's places: same-park candidates, id versus file name, nodes without `sp`.
3. A fixture test of `build/state.py` as it is.
4. `lib/places.py` (identity, id, ledger) with tests, nothing calling it; then `jobs/addplace.py` with fakes and `--dry`.
5. `data-addplace.yml`; a dry run on one state; then `data-state` calls it. The validator rules.

## 9. Decisions
- Decided (owner, 18 Nov): complete creation in one go; a place depends on species, never the reverse; one ledger writer and shape for all kinds, one file per kind (recommended, species side).
- Open: which steps are required for a place (picture, article, outline); the duplicate distances (8 km, 5 km); whether a place with no article is refused; whether `data-state` is rewritten to call the new script or kept alongside.

## 10. Keeping it general
The steps, rules and ledger mention no state and no particular park. A new kind of place (a marine area, a city park) is a new entry in `lib/contracts.py`, not new code; a new source of candidates is a new input, not a new step.
