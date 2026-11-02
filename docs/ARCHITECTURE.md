# Data and loading design (decided 2026-11-01 with the owner)

Why: the page is one file with all places, outlines and the diagram library inside it (about 1.8 MB, 830 KB of it places data). That costs about 650 bytes per place, so 10,000 places would be about 6.5 MB inside the page. The app must keep working as places are added, so code and data are separate and data is loaded in pieces.

## Rules
1. **The page holds code only** (app, styles, start screen). No places data, outlines or diagram library in it.
2. **First-screen places file:** per place only id, name, position, kind and region (about 40 to 60 bytes). Split by continent so a phone fetches only what it shows.
3. **Detail on demand:** card text, pictures, story and food web load when a card is near the screen or a place opens (food webs already do: `webs/`).
4. **Outlines in their own files:** the world outline first; country and state outlines when you go into a region.
5. **Search has its own file,** fetched in the quiet time after the first screen. Search shows "getting ready" until it arrives (owner agreed).
6. **Offline:** not a promise for all places. The shell (page, icons) and the places you opened are kept by the service worker. Do not add a background download of everything (owner decision).
7. **Nothing is written by two jobs.** Each data file has one job that produces it.

## Steps (one item and one pull request each, measured on the phone profile; skip the measurement only when the change is clearly safe and measuring would take long, the owner agreed this call can be made case by case)
1. Outlines on demand (#227).
2. Places data split into a first-screen file plus detail on demand (#228; replaces #187).
3. Search file (#229).
Also on the list: diagram library (D3) on demand (#186).

## Trade-off
Moving data out of the page means a short wait the first time you open a region, a place or search, instead of a longer wait at the start. The first screen must never wait for these.
