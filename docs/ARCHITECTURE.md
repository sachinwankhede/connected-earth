# Data and loading design (decided 2026-11-01 with the owner)

Why: the page is one file with all places, outlines and the diagram library inside it (about 1.8 MB, 830 KB of it places data). That costs about 650 bytes per place, so 10,000 places would be about 6.5 MB inside the page. The app must keep working as places are added, so code and data are separate and data is loaded in pieces.

## Rules
1. **The page holds code only** (app, styles, start screen). No places data, outlines or diagram library in it.
2. **First-screen places file:** per place only id, name, position, kind and region (about 40 to 60 bytes). Split by continent so a phone fetches only what it shows.
3. **Detail on demand:** card text, pictures, story and food web load when a card is near the screen or a place opens (food webs already do: `webs/`).
4. **Outlines:** the country outlines (145 KB raw) draw the home map, so they stay up front. The US state outlines (125 KB raw) are only needed once you go into the US, so they get their own file loaded then.
5. **Search has its own file,** fetched in the quiet time after the first screen. Search shows "getting ready" until it arrives (owner agreed).
6. **Offline:** not a promise for all places. The shell (page, icons) and the places you opened are kept by the service worker. Do not add a background download of everything (owner decision).
7. **Nothing is written by two jobs.** Each data file has one job that produces it.

## Steps (one item and one pull request each, measured on the phone profile; skip the measurement only when the change is clearly safe and measuring would take long, the owner agreed this call can be made case by case)
Order changed after measuring: the places data is the big piece (about 830 KB raw), the state outlines only about 125 KB raw (roughly 0.2 s on the phone profile), so places data goes first.
1. Places data split into a first-screen file plus detail on demand (#228; replaces #187).
2. Search file (#229).
3. US state outlines on demand (#227).
Also on the list: diagram library (D3) on demand (#186).

## Trade-off
Moving data out of the page means a short wait the first time you open a region, a place or search, instead of a longer wait at the start. The first screen must never wait for these.

## Photos are data too (added 2026-11-02)
Findings: to open one place the app downloads a list for all 4,802 species (644 KB raw, 176 KB gzip) and, at start, a list for all 1,144 places (601 KB raw, 119 KB gzip). A place needs about 30 species entries.
Rules:
1. **A picture entry belongs to the thing it shows.** A place's own file carries the entries of its own species (about 5 KB); a card's picture entry travels with the card data. No global list is needed to open a place (#237).
2. **Our own small copies.** A GitHub job downloads each species picture once, shrinks it (about 96 px WebP), keeps credit and licence, and writes one packed file per place (#238). Credits stay in the metadata files and are still shown.
3. **Short, stable addresses** (by id or hash), not long Wikimedia paths repeated twice per entry.
4. **Global lists are only for search or review jobs,** never read to open a place.
5. The photo jobs keep one writer per file and open pull requests that the owner merges.
