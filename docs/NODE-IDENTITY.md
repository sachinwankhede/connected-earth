# What a food-web node is: the target for the override cleanup (#1061, #1038), 22 Nov 2026

Part of #1061 (and #1038, #887). Owner decisions, 22 Nov: the target and order below are agreed; **a place cannot be a node**; find why it appeared in the first place. Read with `docs/ADD-SPECIES.md` (how rows are added), `docs/ADD-PLACE.md` (a place's food web) and the issue #1061 (the earlier rulings).

## 1. The need
Every node in a place's food web should take its name, article, picture and meaning from **one row** of the shared species table, and carry no identity of its own. A node says only which row it is (`sp`), where it sits (`xh`) and, in `desc`, what it is in this place. Today 1,096 nodes keep a `name` or `wiki` of their own (934 and 250 override limits in `build/validate_data.py`). Each override means the table is missing a row, has two rows for one page, has a row made for one place's wording, or a node points at the wrong row.

## 2. The target (invariants)
These are written so that a validator can check each one.

- **I1. A node is a row.** Every node's `sp` is an existing row of the species table. (Holds today.)
- **I2. A node has no identity of its own.** No `name` and no `wiki` on a node. The limits of `build/validate_data.py` go down to zero. A node's `desc` carries what is specific to its place.
- **I3. One page, one row, across kinds.** A Wikipedia page is the article of at most one row in the species table, and of no place. Rows that share a page today (the "Rain" and "Decomposers" pages of #1061) are merged.
- **I4. A place is never a node.** No row's page is a place's own article (its name or its picture article), and no node's article is one. A place is a place in `data/places/`; a row is a species, a group or a kind of resource (water, ice, soil, fire). A named geographic feature that is not a place of ours (a sea, a glacier, a desert) is a resource row like any other kind of water, ice or land, under the test of #1061: a separate article, a licensed picture, `cat` set (owner, 22 Nov: "unless it is a place"). Being specific to one region is not a reason to refuse it.
- **I5. A row is complete.** Picture, summary and, for a taxon, taxonomy (the admission rules of `lib/contracts.json`); a node that would need a row that cannot be made uses the nearest row.
- **I6. It stays true.** The add and update processes (`docs/ADD-SPECIES.md` sections 12 and 12.4) enforce I1 to I5 for every new place, node and row, so an override cannot come back.

## 3. Why a place appeared as a node (root cause)
**What was measured (22 Nov).** 29 rows of the species table have a page that is the name or picture article of a place, 26 of them resource rows: for example `lake-water` (page Lake Titicaca), `crater-lake-water` (Crater Lake), `floodwater` (Iberá Wetlands), `long-snowy-winters` (Mount Paektu), `deep-oxygenated-water` (Lake Baikal). Each of these is used by exactly one place, the place the page names. Five nodes keep a wiki override that is a place page: `xluxembourg/water` (Upper Sûre Lake), `xafghan/ice` (Band-e Amir National Park), `xisrael/water` (Hula Valley), `xnkorea/soil` (Mount Paektu) and `npgatesarctic/soil` (Tundra). The node pictures of #976 are keyed by the slug of a node's `wiki` title. The git history that would show who wrote them is a squashed import, so the authors' intent is not recoverable; the rest is read from the data and the mechanism.

**Cause, as far as the evidence goes.** A node is the only place in the data where a place can say what its water, ice or soil is like, and the node's `wiki` is the only handle that gives it a picture and an article. So when a place's web needed "the water of this lake", the wording went into a node override or into a new row made for that one place, and the page that fitted best was the place's own article. The table had no rule that a row is a concept used by many places and that its page is never a place, so nothing refused it. The new-row candidates of the override report repeat the pattern: Band-e Amir National Park, Iberá National Park, Upper Sûre Lake and Hula Valley are each the own article of the place whose node asked for them.

**What was missing:** the rule (I4), a check that fails when a row or node article is a place, and a creation path that refuses it. The add process, with the cross-kind identity check, is that path.

## 4. What this changes in the plan
- **Four candidates leave the add batch:** Band-e Amir National Park, Iberá National Park, Upper Sûre Lake, Hula Valley. Their nodes use the nearest generic row (ice, fire, water) and say the rest in `desc`. This **supersedes the 18 Nov example** in #1061 that named Upper Sûre Lake and Hula Valley as new rows: on 22 Nov the owner ruled that a place cannot be a node, and both pages turned out to be the own article of the place that asked for them.
- **The 26 resource rows named for a place are a larger job than overrides:** each is one place's wording as a row. The cleanup repoints that node to the generic row (water, ice, snow, soil), keeps the place's detail in `desc`, and retires the row. This is counted in the audit before any change.
- **A node's picture can change** when its override or row goes: the generic row's picture replaces the place-specific one. The audit lists the picture before and after (the correction in #1061).
- **Identity is checked across kinds:** `identify` in `lib/species_rows.py` compares only rows of the same kind today. It gains a check against the place articles, so the add job refuses a place page (`reason: place`).

## 5. Order of work (agreed, 22 Nov)
1. This document, and the update operation of `docs/ADD-SPECIES.md` section 12.4.
2. Done (22 Nov): the override report adds up to 1,096 nodes (nearest 746, repoint 125, new-row 148, ambiguous 64, cross-kind 10, place 3). The "nearest" sample shows the node name is often better than the row name (Elk row, "Red deer" node), so **the row name is decided per row before any override is dropped**. Checks come first (22 Nov, owner: hand edits are fine for this cleanup, but the checks must stop bad data being created): `build/validate_data.py` `page_errors` caps pages held by two rows (151) and rows whose page is a place (27); both only go down.
3. The place-level edit: an update of a place's food web (`docs/ADD-PLACE.md`, section 12) with the checks of the add process and a reference check (journey stops that name the node).
4. The cross-kind identity check, then `data-addspecies` for the pages that really need rows (without the four place pages).
5. Merge the shared rows (I3), repoint, retire the place-named rows, lower the limits to zero, and add the validator rules for I2 to I4.

## 6. Open
- Whether named geographic features that are not our places (Caribbean Sea, Chukchi Sea, Syrian Desert, Fedchenko Glacier) stay resource rows under the 18 Nov test; this document keeps the 18 Nov decision for them.
- Whether the 3 taxon rows whose page matches a place name are real conflicts or coincidences of a common name (checked in the audit).
