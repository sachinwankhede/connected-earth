# Moving a place from the pilot to the main app

Agreed rule (Oct 2026). Places are drafted in `data-auto/` (shown in the pilot). A place moves to `data/` (main) when all of these hold:

1. **Species.** They come from an official list for that place (for example NPSpecies), or from sightings inside the park outline when no official list exists.
2. **Links.** Every feeding link has a GloBI record at species, genus or family level, shown in the place's evidence list. Nothing obviously wrong.
3. **Spot check.** 10 random links from the batch are checked against published sources. More than one obviously wrong means the batch does not ship (wrong ones are fixed either way).
4. **Family-level links.** No more than 60% of a place's links may rest only on a family-level GloBI record (the eater is recorded eating the plant's family, not that species); such places stay in the pilot.
5. **Floors.** With an official list: at least 8 species, 3 plants, 10 links. Without one: at least 12 species, 5 plants, 15 links.
6. **Checks.** `build/validate.py` reports no errors and the test suite passes.
7. **Photo.** A stored photo with a credit line, or the plain icon when Wikipedia has none.

All places on main look alike (no visible tiers); the evidence list carries the detail.
Passing batches are merged without asking; each batch is one commit so it can be reverted. Failing places stay in the pilot.

`python3 build/promote_check.py [ids...]` prints which places pass.

## Shared species table
`data/species.json` has one row per species (key = lowercase Latin name): usual name, wiki page, icon, description, trophic level, category, badge.
Place files keep only each species' id, position and whatever differs from its row. To fix a name, photo page or icon for every place, edit the row.
After generating or editing places, run `python3 build/species.py pack`; CI fails if the files are not packed.

## On-demand loading
The page carries only a light index of each place (name, location, species names, counts). A place's full web (species, links, evidence) lives in `webs/<id>.json`, written by `python3 build/build.py --all` and fetched the first time the place is opened. Commit `webs/` with the built pages; CI fails if they are stale.

## Tests and budget
`npm run test:quick` (about 1 minute) for everyday changes; `npm test` (about 3 minutes) before anything is called done; CI runs the full set. `npm run budget` fails if the pages or data grow past the limits in `build/budget.py`. Park outlines are one small file per park in `data/outlines/<id>.json`, fetched when the park opens (written by `pipeline/bounds.py`; no file means no outline). `pipeline/splitbounds.py` converts the old single `data/bounds.json` if a branch still has one.

## Adding a state
`python3 build/state.py IL --top 25` seeds the largest state parks from PAD-US, drafts species (GBIF) and feeding links (GloBI), generates the places, adds them to the pilot (`data-auto/`), packs the shared species table and fetches outlines, then prints which places pass the promotion floors. Add `--scratch` to try it without touching the repo. Photos and Wikipedia lines are slow (Wikimedia throttles): run `pipeline/fetch_all.sh` and leave it going. Promote with `python3 build/promote.py --local` after the 10-link spot check.
Known limit: species are sightings within a circle around each park point, not strictly inside its outline. Small parks next to busy places can pick up neighbours' sightings; querying by the real outline (now stored in `data/bounds.json`) would tighten this.
