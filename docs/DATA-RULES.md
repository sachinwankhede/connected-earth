# Data rules: one list, each rule enforced where the data is made (26 Nov 2026)

Part of #1061, #1023 and #1211. Written after the bad-data cleanup of 22 to 26 Nov (#1142, #1038, #1138, #1183). The cleanup took many rounds because each rule was found by looking at the result, fixed once, and not written down where a check could hold it. This page lists every rule we hold or have decided, says where it is enforced today and where it is not, and sets one plan to close every gap together. Read with `docs/NODE-NAMES.md` (names), `docs/NODE-IDENTITY.md` (what a node is) and `docs/CREATION-PATHS.md` (how things are created).

**Enforcement levels.** `gate` = fails the pull request check (`build/validate.py`, `build/validate_data.py`, `lib/photo_registry.py validate`, tests). `audit` = found only by an audit job that someone dispatches (`data/audit/*.json`, the data dashboard). `none` = nothing checks it. Only `gate` counts as enforced. **Principle: a rule is closed only when a bad write is refused at the door (the one writer) and a bad edit fails `gate`. The audit is a drift detector for what Wikipedia changes after we wrote the row, never the main defence.**

## 1. Rows (the master list: taxon, group, resource)

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| R1 | A row maps to one Wikipedia page, and a page maps to one row per kind. | owner 18 Nov | audit (shared_page flag) | Not a `gate` error; two rows can share a page. |
| R2 | A row exists only if its page is a separate article (not a redirect, disambiguation, section or missing page). | owner 18 Nov | audit | Nothing refuses it at creation. |
| R3 | The page must be about the row: a species row on that taxon's page; a resource row on the concept (Stream, Tide), not on a named place or another kind of thing (Limpopo River for "Rivers", Oxisol for "Poor acidic soils"). A named feature may have its own row only when the row is named for it. | owner 18 and 24 Nov; reading confirmed 26 Nov: refuse a resource row only when its name and page disagree ("Rivers" on Limpopo River); "Upper Sûre Lake" on Upper Sûre Lake stays | audit (partly) | The "page is about the name" check is by hand today. |
| R4 | A species row's page is not a genus, family or other higher rank, and a genus row is not on a species page (sorghum). | owner 24 and 26 Nov | audit | Species-on-genus is not flagged (#1211); the `repoint` status proposes the opposite. |
| R5 | Name: the row name is the Wikipedia article title (brackets dropped); a genus row takes the common name if Wikipedia has one, else the Latin genus name; a common-name page keeps the common name. | owner 22 and 26 Nov, `docs/NODE-NAMES.md` | audit (needs the web) | Not checked at creation. |
| R6 | No row is created for a spelling, a regional name or a wording of an existing species; no row is created only to hold text. | owner 17 Nov | none | |
| R7 | Subspecies, breeds and populations may have a row of their own if they have a separate article and a licensed picture; the description says what it is a form of. | owner 18 Nov | none | |
| R8 | A new row arrives complete: picture, summary, taxonomy entry. A missing licensed picture means no row, and the node uses the nearest existing row. A conservation status is optional. | owner 18 Nov | none | #1023 not built; rows can be created bare. |
| R9 | A row is of one kind: resource rows live in `data/nodes/rows/` with `cat` abiotic or decomp; species and group rows in `data/species/rows/`. | #976 | gate | |
| R10 | A row a place uses is not deleted; a row no place uses is deleted. | owner 24 Nov | audit (no_node) | Not a `gate` error. |
| R11 | A synonym is not kept as a second row: two rows on one Wikidata item are merged into one (Dalibarda into Rubus). Wikipedia merges articles after the fact, so this is re-checked. | owner 23 Nov | audit | The re-check has no schedule. |
| R12 | Row ids are frozen once written; the id derives from the Latin name, with `-2` on a clash. | #276 | gate (build) | |

## 2. Nodes (a box in one place's food web)

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| N1 | A node names its row by `sp`; it keeps no `name` or `wiki` of its own. | owner 18 Nov | gate (limits are 0) | |
| N2 | A node keeps its own `desc` when the place needs a different text; the row text is shared. | #1038 | none needed | |
| N3 | Every node is linked to at least one other node. | validator | gate | |
| N4 | Node ids and names are unique inside a place. | validator | gate | |
| N5 | Resource nodes: a place has at least one abiotic and one decomposer node. | #1138, owner 24 Nov | gate | |
| N6 | A node picture entry exists only for a concept some node shows. | #1183 | audit (orphans) | `NodePhotos.check()` does not list orphans. |

## 3. Places

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| P1 | 10 to 34 species nodes. | validator | gate | |
| P2 | File name = id; id is lowercase letters and digits; country and state are ids from `geo.json`. | validator | gate | Two units with the same short id clash silently (`state.py`). |
| P3 | 1 to 8 sources with title and https URL; a story is required when `matters` is set; tier and side are valid. | validator | gate | |
| P4 | The food web matches its stamped record (`place_inputs`). | validator | gate | |
| P5 | No place twice under two ids (sdponca and neponca). | DATA-PLAN lesson 6 | none | |
| P6 | A place is created complete (outline, picture or a recorded reason, a story with its research record) behind admission rules. | owner 18 Nov | none | 320 places have a story and no research record (warning). |

## 4. Journeys

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| J1 | A journey names species by id, and its ends are real nodes of real places. | `CREATION-PATHS.md` | partly (gate for stops, none for the end node) | |
| J2 | A row or place a journey ends at is never removed by a cleanup; it is kept and listed. | #1061 | removal tool | |

## 5. Pictures, credits and names of authors

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| X1 | Licences: Wikimedia CC0, CC BY, CC BY-SA, public domain; GBIF CC0 and CC BY with a named author. | #421 | gate (`photo_registry.py validate`) | |
| X2 | Every picture has a named author; "Unknown author" is a licence doubt for the owner. | #421 | gate / dashboard | |
| X3 | Picture files and lists agree (the job that writes a file writes its list entry). | owner 14 Nov, #727 | gate | |
| X4 | A picture is looked up by the article, and a resource row with no usable picture shows its icon. | #976 | build | |

## 6. Removing data (every removal goes through one path)

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| D1 | No data is better than bad data: a row that fails R1 to R5 is removed, not patched, with everything that depends on it. | owner 23 Nov | by hand | |
| D2 | A removal keeps every place valid after it: 10 species, every node linked, an abiotic and a decomposer node, the journey ends. A node left without links is kept and relinked, never silently dropped (the palm, welwitschia and fire nodes were lost to this). | #1142 | removal tool and its test (since 26 Nov) | Tools other than `strictrows.apply` can still delete directly. |
| D3 | A removal also removes the row's diet records, taxonomy, conservation and picture entries, its audit entries and its node pictures. | #1061 | `validate_data` fails on leftovers | The orphan node picture cleanup is a separate job. |
| D4 | A removal is recorded in `data/audit/strictrows.json` with its reason. | #1061 | gate | |

## 7. Process (how data and code are changed)

| # | Rule | Source | Enforced now | Gap |
|---|---|---|---|---|
| Q1 | Data by jobs and pull requests; agents do not hand-edit data folders. | CLAUDE.md | convention | |
| Q2 | Run `build/validate.py` with the place files, as CI does; with no arguments it checks nothing. | 26 Nov | none | Make the no-argument run fail or check all. |
| Q3 | A test does not depend on a real limit or on real data (fixtures, or it sets its own limits). | CLAUDE.md rule 9 | convention | |
| Q4 | A test that stubs with `page.route` blocks the service worker. | #1078 | convention | Audit the other stubbing tests. |
| Q5 | Combine related changes in one pull request when they use the same checks. | owner 26 Nov | convention | |
| Q6 | A pull request's audit and `STATE.md` edits conflict when two are open; merge main before the last push. | 26 Nov | none | Keep audit changes out of feature branches. |
| Q7 | After a merge, read the `deploy` result. | CLAUDE.md | convention | |

## 8. What to build, once

Instead of fixing rule by rule, build these together so each rule above is closed at the writer and at `gate`.

1. **One row writer** (`lib/rows.py`, with `check()`): the only code that creates, renames, repoints, merges or removes a row. It enforces R1 to R8, R11 and D1 to D4, and logs a refusal with its reason. Jobs and tools call it; none writes a row file directly. (Merge and removal use the paths now in `jobs/mergerows.py` and `jobs/strictrows.py`.)
2. **`gate` rules (offline)**: R1 and R9 as errors (two rows of one kind on one page; resource rows in the right folder); R10 (unused row); N6 (orphan node picture); P2 (clashing place id); Q2 (the validator refuses to run with no places). The web-dependent rules R2 to R5 are checked inside the writer when a data job creates the row, and by the audit as a drift check.
3. **Fix the audit rules** so a clean audit means clean data: flag a species row on a genus page (R4), drop the `repoint` proposal for species rows, let the check say "genus row, Latin name" for rows whose proposed name is a species' common name.
4. **Schedule** the identity and name audits weekly as the drift detector (R11), and open an issue when the dashboard count is not zero.
5. **Done when:** every row of the tables above that says `none`, `audit` or `convention` has a test, and a deliberately bad row (shared page, wrong rank, bare row, a removal that orphans a node) fails `gate` or is refused by the writer.

## 9. Owner decisions to confirm

- Decided (owner, 26 Nov): the admission rules R2 to R8 as drafted (what is refused; refused nodes use the nearest row; the refusal is logged).
- R3 is decided (owner, 26 Nov): a resource row is refused only when its name does not match its page; a named feature with its own matching row stays.
- Audit cadence: weekly (owner, 26 Nov: monthly is too far).
