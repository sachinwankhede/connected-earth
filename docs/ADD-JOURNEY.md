# Adding a journey: the one standing process, whole or not at all (design, 22 Nov 2026)

Part of #1023 (how a place, a species and a journey are created). **This is the standing process for every journey that will ever be added.** Read with `docs/ADD-SPECIES.md` (the frame) and `docs/ADD-PLACE.md`. Facts about today's code come from `docs/CREATION-PATHS.md` (#1054, unmerged); claims not checked in code are marked **unverified**.

A journey is the route of one species between two places (for example a flamingo between two lakes). It depends on **both** other kinds: the species by id and the places by id. Neither depends on a journey.

## 1. What exists today
No job writes a journey. `jobs/journeys.py` ranks candidate species, `jobs/journeyresearch.py` gathers source text, and a person or agent writes `data/journeys/<id>.json` by hand (`docs/PROMOTION.md`, "Finding more journeys"). There are 19 files plus `config.json`. The cover picture comes later from `lib/journey_photos.py`, keyed by journey id.

Where it goes wrong today:
- The `id` is typed. It must be non-empty and not repeated; it is not required to equal the file name (**unverified** for all files).
- `ends[].eco` is a place id and is checked. `ends[].node` is a node id inside that place and is **not** checked.
- The species is named only by `imgwiki` (a Wikipedia title) and free text; there is no species id. Renaming a node or merging two species rows would break a journey silently.
- `pos` is typed per file; a duplicate or gap is not reported (**unverified**).
- Nothing tests the creation path, because it is by hand.

## 2. The shape
**A script that checks and writes, run by one workflow**, as for species and places. `jobs/addjourney.py` takes candidates and runs the steps below in order. Identity failing stops the candidate; every other step is run and recorded; the file is written only when every required step passed. The text itself (route, why it matters, sources) is still written by a person or the agent; the script is what refuses a draft that does not hold together.

A candidate is a draft: `{id, species (a species id), ends: [{place id, node id, role}], route text, sources}`. It names the species by id, never by Latin name or title.

| Step | Check | On failure |
|---|---|---|
| 1 Identity | The id is new and equals the file name. No existing journey has the same species and the same pair of places. | Refuse: `duplicate of <id>`. |
| 2 Species | The species id is an existing row with all its data (the species process). `imgwiki` and the name are read from the row, not typed. | Refuse: `no species`. |
| 3 Places | Every end's place id exists, is not `level: local`, and the two ends are different places. | Refuse: `no place` or `same place`. |
| 4 Nodes | Every end's node exists in that place **and its `sp` is this species**. A mismatch is the case today's data cannot detect. | Refuse: `node missing` or `species mismatch`. |
| 5 Source | The route is supported by the source text (the rule of `docs/PROMOTION.md`: a real route only where the source supports it); at least one source with a licence in `lib/allowed_sources.json`. | Refuse: `no source`. |
| 6 Position | `pos` is assigned by the process (next free value), never typed. | Not an error. |
| 7 Picture | A cover picture with an accepted licence (`lib/journey_photos.py`, the sources of #421). | Refuse: `no licensed picture`. |
| 8 Commit | The file and the picture record are written together; file first, lists last. | The whole candidate is dropped. |

Required steps live in `lib/contracts.py` (the picture is the first candidate for "wanted, not required"; the first run decides).

## 3. Integrity and duplicates
Identity is decided before anything is written: same id, same file name, or same species and same two places is a duplicate, reported and never merged. The validator gains, as errors for journeys added by this process: `id` equals the file name; `pos` unique; every `ends[].node` exists in its place; the node's `sp` equals the journey's species. The 19 existing files are measured first by a read-only audit; the ones that fail are held by a count limit that only goes down until they are fixed. Other guards: all-or-nothing commit, idempotent create, one concurrency group, validators on the finished tree before a pull request opens.

Because a journey names species and nodes by id, a later merge or rename of a species row or a node is caught by the validator instead of breaking a journey silently. This is why the 19 existing journeys get a species id (a one-off job that matches `imgwiki` to a row; ambiguous ones go to a person), while the app keeps reading `imgwiki` until the check proves it matches.

## 4. Schema and model
New schemas in `build/schemas/`, each with a real-writer entry in `tests/data/writer_schema_test.py`: the journey file (species id, ends as place id and node id, `pos`, route, sources), the journey picture credit and the ledger. Model rules (species exists, ends distinct, nodes match, `pos` unique, id equals file name) are in `build/validate_data.py` and read limits from `lib/contracts.py`.

## 5. Input, entry points, and GitHub
1. **A draft file** given to the workflow (by hand), the normal path today made safe.
2. **The ranking:** `jobs/journeys.py` and `jobs/journeyresearch.py` keep producing candidate lists; their output is a list of species ids (not Latin names) so a candidate can be created without a lookup by name.
3. **The refusal ledger:** refused drafts whose hold has expired (a source or picture may have appeared); by hand first, then scheduled.

`.github/workflows/data-addjourney.yml` (owner-merged): `workflow_dispatch` with the draft path, `dry` (default yes); `GITHUB_TOKEN` only; one data pull request listing the sources, licences, refusals and the spot check. A dry run checks everything and writes nothing.

## 6. The ledger
Same shape as species and places, one file for journeys, one writer. Counted by step, it shows what blocks most journeys (for example `species mismatch`, `no licensed picture`).

## 7. Risks
- **Node ids may change:** they are built from common names and used by journeys; the validator turns a rename into a visible failure. Re-keying nodes is out of scope.
- **Species merges (#1061) touch journeys:** the cleanup must run the journey check before it merges, or journeys that point at a merged row fail.
- **The route text is judgment:** the script cannot prove a route is true; it checks that sources exist and that the structure holds, and the pull request spot check covers the rest.
- **Few journeys:** 19 files; the process is small, so a heavy workflow is not justified before the species and place processes exist.

## 8. Order of work
1. This document read and decided (owner). Species process first, place process second, because both are inputs.
2. Read-only audit of the 19 journeys: id versus file name, `ends[].node` exists, node's species matches `imgwiki`, duplicate `pos`. Its numbers decide the validator limits.
3. Validator rules for what the audit finds already clean.
4. `lib/journeys.py` (create, check, ledger) with tests, nothing calling it; then `jobs/addjourney.py` with fakes and `--dry`; then the species id on the 19 existing files.
5. `data-addjourney.yml`; a dry run on one draft.

## 9. Decisions
- Decided (owner, 18 Nov): complete creation in one go; one ledger writer and shape for all kinds, one file per kind (recommended, species side).
- Open: whether a cover picture is required; whether the 19 existing journeys get a species id before the process exists; whether a journey may have more than two ends.

## 10. Keeping it general
Steps, rules and ledger mention no species, no place and no route. A new kind of journey (a seasonal range, a migration with several stops) is a new entry in `lib/contracts.py`, not new code.

## 11. The interface
Same REST-like contract as the other kinds: `POST` a candidate (with `dry`), a response with `status` (`added`, `exists`, `refused`), `id`, every step's result and a `reason`; idempotent; read calls for the record and the ledger. The shape, the function behind it (`add(kind, candidate, dry)`), the command line and the optional Cloudflare Worker are in `docs/ADD-SPECIES.md`, section 12. The steps of this document are the `steps` of the response.
