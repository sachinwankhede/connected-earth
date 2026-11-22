# Adding a journey: the one standing process, whole or not at all (design, 22 Nov 2026)

Part of #1023 (how a place, a species and a journey are created) and #1080 (a journey is a network, not a pair). **This is the standing process for every journey that will ever be added.** Read with `docs/ADD-SPECIES.md` (the frame) and `docs/ADD-PLACE.md`. Facts about today's code come from `docs/CREATION-PATHS.md` (#1054, unmerged) and from reading the build and the app on 22 Nov; claims not checked in code are marked **unverified**.

A journey records a **connection between food webs**: organisms moving between places, or matter flowing between them. It is a set of **stops** (a place plus a node in that place's web) joined by **legs**. A journey depends on the places and, for a species journey, on the species by id. Neither depends on a journey.

## 1. What exists today
No job writes a journey. `jobs/journeys.py` ranks candidate species, `jobs/journeyresearch.py` gathers source text, and a person or agent writes `data/journeys/<id>.json` by hand (`docs/PROMOTION.md`, "Finding more journeys"). There are 19 journeys plus `config.json` (22 Nov): 17 of `type: species`, each with `ends`, a list of two `{eco, node}`; and 2 of `type: flow` (`dust`, `nutrients`), each with a directed `from` and `to`. The cover picture comes later from `lib/journey_photos.py`, keyed by journey id.

What is checked and what is not:
- `build/build.py` fails the build when an end's node (`ends[]`, `from`, `to`) does not exist in that place's food web. The place id is checked as well.
- Not checked: that the node's species is the journey's species. The species is named only by `imgwiki` (a Wikipedia title) and free text, never by species id, so renaming a node or merging two species rows would break a journey silently.
- The `id` is typed; it is not required to equal the file name (**unverified** for all files). `pos` is typed per file; a duplicate or gap is not reported (**unverified**).
- Nothing tests the creation path, because it is by hand.

Where the code assumes exactly two ends (read on 22 Nov): `src/app/maplibre.js` (`arcEnds` reads `ends[0]` and `ends[1]`; `actOf`), `src/app/map-view.js` (`ecoEnds`) and `src/app/data.js` (the node-to-journey index `XL` sets each end's "other end" to the opposite one), whose users are `graph.js`, `loading-controls.js` and `panel.js`. The build passes journeys to the app as `links.cross`. The app also reads a flow with only a `to` and an outside `src` point; no file uses it (**unverified** that nothing else does).

The data already shows the pair model splitting real routes: `osprey` and `chesosprey` both end at the Amazon osprey node, and `greenturtleA` and `greenturtleB` both start at the Biscayne turtle node. Each is one migration system recorded as separate pairs.

## 2. What a journey is, and the model
**Concept (owner, 22 Nov).** Food webs are connected by two things: organisms that move between them (the same individuals sit in both webs) and matter or energy that flows between them (a river, dust, spawning fish). Two other things are not modelled as connections: a shared species (separate populations only resemble each other; a shared species is a similarity, not a link) and a shared climate or a nesting of habitats.

**Model.** A journey is a small network:

| Part | Meaning | Rule |
|---|---|---|
| `stops` | a list of `{eco, node}`: a place id and a node id in that place's web | at least two; each place once; each node must exist |
| `legs` | a list of `{a, b, dir, when?}`: `a` and `b` are positions in `stops`; `dir` is `both` (species: the animals go both ways over the year) or `ab` (a flow, or a one-way route); `when` is an optional sentence | every stop is in a leg; the legs form one connected network; no leg to itself; no repeated leg |
| `type` | `species` or `flow` | a species journey has a species id and every stop's node has that `sp`; a flow journey has no species |

A route with stopovers is a chain of legs. Several origins into one destination (the osprey) are several legs into one stop. A flow that fans out is several `ab` legs from one stop. **Today's files are the smallest case:** a species pair is two stops and one `both` leg; a flow is two stops and one `ab` leg. They move over without loss (section 5). Roles such as "breeding" or "wintering" are not a field: direction and the `when` sentence say it, and a field nothing reads is not added.

## 3. The shape of the process
**A script that checks and writes, run by one workflow**, as for species and places. `jobs/addjourney.py` takes candidates and runs the steps below in order. Identity failing stops the candidate; every other step is run and recorded; the file is written only when every required step passed. The text itself (route, why it matters, sources) is still written by a person or the agent; the script is what refuses a draft that does not hold together.

A candidate is a draft: `{id, type, species (a species id, for a species journey), stops: [{eco, node}], legs: [{a, b, dir, when?}], route text, sources}`. It names the species by id, never by Latin name or title.

| Step | Check | On failure |
|---|---|---|
| 1 Identity | The id is new and equals the file name. No existing journey has the same type, the same species and the same set of stops (a duplicate). A journey of the same species that shares a stop with another is **not** refused: it is reported as `overlaps <id>` for a person to decide whether the two are one network (`osprey` and `chesosprey`). | Refuse: `duplicate of <id>`. |
| 2 Species | Species journeys only: the species id is an existing row with all its data (the species process). `imgwiki` and the name are read from the row, not typed. | Refuse: `no species`. |
| 3 Places | Every stop's place id exists, is not `level: local`, and no place appears twice. | Refuse: `no place` or `same place`. |
| 4 Nodes | Every stop's node exists in that place **and, for a species journey, its `sp` is this species**. A mismatch is the case today's data cannot detect. | Refuse: `node missing` or `species mismatch`. |
| 5 Legs | At least two stops; every leg refers to two different stops; no repeated leg; every stop is in a leg; the legs connect all the stops; a flow's legs are `ab`. | Refuse: `bad network` and what is wrong. |
| 6 Source | The route is supported by the source text (the rule of `docs/PROMOTION.md`: a real route only where the source supports it); at least one source with a licence in `lib/allowed_sources.json`. | Refuse: `no source`. |
| 7 Position | `pos` is assigned by the process (next free value), never typed. | Not an error. |
| 8 Picture | A cover picture with an accepted licence (`lib/journey_photos.py`, the sources of #421). | Refuse: `no licensed picture`. |
| 9 Commit | The file and the picture record are written together; file first, lists last. | The whole candidate is dropped. |

Required steps live in `lib/contracts.py` (the picture is the first candidate for "wanted, not required"; the first run decides).

## 4. Integrity and duplicates
Identity is decided before anything is written: same id, same file name, or same type, species and stops is a duplicate, reported and never merged. The validator gains, as errors for journeys added by this process: `id` equals the file name; `pos` unique; every stop's node exists in its place (the build already checks this); for a species journey the node's `sp` equals the journey's species; the network rules of step 5. The 19 existing files are measured first by a read-only audit; the ones that fail are held by a count limit that only goes down until they are fixed. Other guards: all-or-nothing commit, idempotent create, one concurrency group, validators on the finished tree before a pull request opens.

Because a journey names species and nodes by id, a later merge or rename of a species row or a node is caught by the validator instead of breaking a journey silently. This is why the 17 existing species journeys get a species id (a one-off job that matches `imgwiki` to a row; ambiguous ones go to a person), while the app keeps reading `imgwiki` until the check proves it matches.

## 5. Schema, and the move of today's files
New schemas in `build/schemas/`, each with a real-writer entry in `tests/data/writer_schema_test.py`: the journey file (type, species id, stops, legs, `pos`, route, sources), the journey picture credit and the ledger. Model rules are in `build/validate_data.py` and read limits from `lib/contracts.py`.

**The build is the one place that knows both shapes during the move.** It reads a file with `ends` or `from`/`to` (today) or with `stops`/`legs` and hands the app one shape (`stops` and `legs`). Nothing in the app guesses which shape a file has, and no data job has to run before the app changes.

The move of today's 19 files is mechanical and lossless: `ends` becomes two stops and one `both` leg; `from`/`to` becomes two stops and one `ab` leg; `pos`, text, sources and `imgwiki` are unchanged. It is a one-off data job that opens one pull request, with a test that the build output is the same before and after for every file (apart from the shape). Merging `osprey` into `chesosprey`, or the two green turtle files, changes ids and covers and is a decision per case, never part of the mechanical move.

## 6. Input, entry points, and GitHub
1. **A draft file** given to the workflow (by hand), the normal path today made safe.
2. **The ranking:** `jobs/journeys.py` and `jobs/journeyresearch.py` keep producing candidate lists; their output is a list of species ids (not Latin names) so a candidate can be created without a lookup by name. The coverage report of section 8 adds candidate stops.
3. **The refusal ledger:** refused drafts whose hold has expired (a source or picture may have appeared); by hand first, then scheduled.

`.github/workflows/data-addjourney.yml` (owner-merged): `workflow_dispatch` with the draft path, `dry` (default yes); `GITHUB_TOKEN` only; one data pull request listing the sources, licences, refusals and the spot check. A dry run checks everything and writes nothing.

## 7. The ledger
Same shape as species and places, one file for journeys, one writer. Counted by step, it shows what blocks most journeys (for example `species mismatch`, `no licensed picture`).

## 8. Finding missing journeys
A journey is a connection that exists in nature, so a missing journey is a connection the data does not yet hold. The data can propose candidates; it cannot prove them.

- **Species candidates.** For a species that moves between habitats, list the places whose web has a node of that species and that are not a stop of any journey of that species. A shared species alone is not evidence of a link (owner, 22 Nov), so the report only lists species with evidence of movement (migratory status or range data) and only places that fit the ranges (for example breeding and wintering areas). The evidence source is **unverified**: it must be a host already in `lib/allowed_sources.json`, or its addition is an owner decision.
- **Flow candidates.** Nodes for matter that moves (dust, sediment, nutrients, water) in places that physically connect, such as a river and the sea it enters. The relation between places (a basin, a coast) is **unverified**: nothing in the data says which place drains into which.
- **The report is read-only.** `build/` script, like `override_report.py`: it prints the candidate stops and what already exists, and changes nothing. A candidate becomes a journey only through the process of section 3, with a source text.

## 9. Risks
- **Node ids may change:** they are built from common names and used by journeys; the validator turns a rename into a visible failure. Re-keying nodes is out of scope.
- **Species merges (#1061) touch journeys:** the cleanup must run the journey check before it merges, or journeys that point at a merged row fail.
- **Repointing a node's species or dropping its overrides can break a journey stop,** because the stop checks the node's species. The edit that does it must list the journey stops that name the node before it writes (the check of #1061).
- **The route text is judgment:** the script cannot prove a route is true; it checks that sources exist and that the structure holds, and the pull request spot check covers the rest.
- **A change of model touches three layers:** data files, the build and the app (map arcs, node cross-links, credits). They change in the order of section 10, each in its own pull request, with the app tested on both a pair-shaped and a network-shaped journey.
- **Few journeys:** 19 today; the process is small, so a heavy workflow is not justified before the species and place processes exist.

## 10. Order of work
1. This document read and decided (owner). Species process first, place process second, because both are inputs.
2. Read-only audit of the 19 journeys: id versus file name, node's species matches `imgwiki`, duplicate `pos`, and the list of journeys that share a stop (`osprey`/`chesosprey`, `greenturtleA`/`greenturtleB`). Its numbers decide the validator limits.
3. Build reads both shapes and hands the app `stops` and `legs`; the validator checks the network rules. With the app change in the same release (the build output and its reader must agree): the map draws one arc per leg, a node's cross-link lists the other stops, credits and panels read the stops. A UX change: `perf-ab`, tests on a pair and on a three-stop journey.
4. `lib/journeys.py` (create, check, ledger) with tests, nothing calling it; then `jobs/addjourney.py` with fakes and `--dry`; then the species id on the 17 species journeys.
5. The one-off move of today's files to stops and legs (section 5).
6. `data-addjourney.yml`; a dry run on one draft. The coverage report of section 8 can come any time after step 2.

## 11. Decisions
- Decided (owner, 18 Nov): complete creation in one go; one ledger writer and shape for all kinds, one file per kind (recommended, species side).
- Decided (owner, 22 Nov): a journey is not limited to a pair of ends; it has stops and legs. Food webs are connected by movement of organisms and flows of matter; a shared species is not a connection.
- Open (owner, 22 Nov: parked in #1082, to be answered before any journey work starts):
  - whether a cover picture is required;
  - whether the 17 species journeys get a species id before the process exists;
  - whether a leg carries its own season sentence (`when`) or the journey's one `when` is enough;
  - whether `osprey`/`chesosprey` and the two green turtle files become one journey each (a decision per case);
  - whether a flow node must be a resource node, and whether a flow may start at a point outside any place (the app reads such a flow; no file has one: drop that branch or model it);
  - whether the build and the app change in one pull request (recommended) or the build first with the app reading both shapes;
  - which source of movement evidence the coverage report may use (section 8).

## 12. Keeping it general
Steps, rules and ledger mention no species, no place and no route. A new kind of journey is a new entry in `lib/contracts.py` (which checks apply to its stops), not new code.

## 13. The interface
Same REST-like contract as the other kinds: `POST` a candidate (with `dry`), a response with `status` (`added`, `exists`, `refused`), `id`, every step's result and a `reason`; idempotent; read calls for the record and the ledger. The shape, the function behind it (`add(kind, candidate, dry)`), the command line and the optional Cloudflare Worker are in `docs/ADD-SPECIES.md`, section 12. The steps of this document are the `steps` of the response.
