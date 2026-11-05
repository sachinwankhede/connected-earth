# Search and species experience (spec, #407)

Status: **agreed** (5 Nov 2026, the owner accepted every proposal below). Items follow this document; if an item and this document disagree, change the document first (as for `docs/DESIGN.md`). Visual rules (back link, rows, fonts, credits) stay in `DESIGN.md`; load and size rules in `ARCHITECTURE.md`.

## Principles
1. **One box.** Places and species are in the same suggestions; the type is shown on every row, never chosen by a mode switch or chips before typing.
2. **Exact first, then well known.** Ranking looks at how exactly the name matches, then at how well known the thing is. Type is not a ranking factor.
3. **Every state says what is true.** Loading, nothing found, failed and limited (offline) each have one plain line. No result screen is silent.
4. **A search is part of the address.** Back, reload and a shared link keep it.
5. **A species is a thing you can open,** not only a filter.
6. **Nothing permanent covers the map;** transient things (the dropdown) close on any choice. Nothing is loaded at start-up for search; small files load when typing starts or a screen opens.

## What people come to do
- **A. A place by name** ("Yellowstone"): type, tap the row, land on the place.
- **B. A species by name** ("osprey", "Pandion"): type, tap the row, land on the species page.
- **C. What lives here:** from a place, to its species, to the species page and its other places.
- **D. Browse without a name:** the Species tab (top species, then groups), and Places and Journeys as today.

## Flows
1. **Typing (dropdown).** From two letters, under the box; 3 rows on a phone, 5 wider. Row: photo (or icon), name, one muted line, chevron, 56 px. Lines: `Place · <state or country>` and `Species · in N places`. Order: exact name, then names that start with the text, then names with a word that starts with it; within equal matches the better known first (places in home-list order, species by number of places). Closes on a tap on a row, Enter, Clear or a tap elsewhere. (Built in #413; the type line for places and exact-first ranking in #424. Within an equal rank places and species take turns by their position in the file, so the type alone never decides.)
2. **Place row** opens the place page. **Species row** opens the species page (#420). (Decided: the species row opens the page and not the map filter.)
3. **Species page (#420).** Photo (thumbnail now, 400 px when one exists, #421), kind line, common and Latin name, the short description when there is one, "Found in N places" as tappable place rows, a "Show on the map" link, share icon, Sources & credits. No eats / eaten-by in version 1. Back goes to where the person came from ("‹ Search" from search).
4. **Enter (results).** The list and map are filtered. A header line says what the result is: for an exact species or place match a header row with the name, the count and a link to its page; otherwise "N places match “text”", also inside a region. Each card carries one muted line saying why it matches ("Has osprey").
5. **Show on the map** (from the species page) filters the map and shows a visible chip "Places with Osprey ✕" instead of an invisible filter. Back or ✕ removes it.
6. **Species tab (#422).** Top species first, then groups, each on demand. The box on this tab filters species only.
7. **Address.** `s=<text>` for a search, `sp=<latin slug>` for a species page, the tab as for places and journeys. Back leaves a species page for the search it came from; Back from a search with text clears it before leaving.

## States
- **Empty box:** nothing (later: the last three searches, kept on the phone only).
- **Typing:** one redraw per keystroke; the previous results stay until the new ones arrive; a "Searching…" line while the index or the local places are still loading (never the "nothing found" text then).
- **Nothing found:** "No places or species match “text”." with Clear. The old "No ecosystems here yet" text is only for an empty region.
- **Index failed or offline:** one muted line "Search is limited right now"; the list still filters on the card text (world places only offline). Retried after 30 s as today.
- **Photo missing:** icon or placeholder, never a gap or another site.

## Matching rules (one place for them)
Words are folded for case, accents and apostrophes; every typed word must start a word of the name; the last word completes as you type. Later: plurals and common spelling pairs, so "elks", "wolves" and "grey" find something. Rare species may be missing from the dropdown (40 per two-letter start) but are always found by a full search.

## On a phone
Input 16 px (iOS does not zoom), a ✕ inside the field only while there is text (a deliberate exception to "no ✕" in DESIGN, which is about navigation), Enter closes the keyboard (`enterkeyhint="search"`), tap targets 44 px or more. The first view has about 5 KB of size budget left, so added page code stays small and everything else loads on demand.

## What we do not do
No "All / Places / Species" chips in the dropdown; no modal; no new button for search; no species list loaded at start; no outside pictures at run time.

## From this spec to items
| Part | Item | State |
|---|---|---|
| Search box on a phone | #409 | done |
| Dropdown | #413 | done |
| Dropdown type line, exact-first ranking | #424 | done |
| Search in the address, Back | #412 | done |
| One redraw, honest states, nothing-found text | #414 | done |
| Species page | #420 | step 1 done (screen, address, Back); steps 2 and 3 to do |
| Result header, "why it matches" line, filter chip | #425 | idea |
| Larger photos, photos for species with none | #421 | idea |
| Species tab | #422 | idea |

**Suggested order:** dropdown type line and exact-first ranking, #412, #414, #420 steps 1 and 2, result header and why line, #421 part A, #420 step 3, #422.

## Decided (owner, 5 Nov 2026)
1. The species row opens the species page.
2. The back link from search says "‹ Search".
3. An exact species or place match gets a header row above the results.
4. The species filter becomes a visible chip.
5. Recent searches come later, not now.
