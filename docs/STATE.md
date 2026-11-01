# Project state (read this first in a new session)

Kept by Claude, reviewed by the owner (Sachin). Update it in the same PR as the work. For what is running right now, read the issue "Project status" (refreshed daily) or run `bash pipeline/status.sh`. Rules for the code and the jobs are in `CLAUDE.md`, `docs/DESIGN.md`, `docs/PROMOTION.md` and `docs/JOURNEYS.md`.

## How we work (decisions)
- Short replies; Sachin tests on a real iPhone.
- Discuss the design before building a workflow or scheduled job. Run one job by hand first to judge quality and timing, then choose a schedule.
- Heavy web pulls run as GitHub Actions jobs, triggered and left in the background. Jobs never merge; they open one pull request.
- Merging to main, deleting branches and closing PRs are Sachin's call. "Yes to N" / "Go ahead" counts as approval of the PRs I listed. Wait for green CI before merging to main.
- UI: follow `docs/DESIGN.md`; avoid buttons (plain links or tappable cards); keep mobile and desktop in sync; test the affected area on both sizes, both directions; the full suite runs in CI only.
- Never hand-edit built files (index.html, pilot/index.html, sw.js, webs/).
- Story batches 25 to 40 places: story at most 60 words, why-it-matters at most 40, every number checked against the research text; park summary one Wikipedia sentence; journeys only where the source text supports a real route; 60% family-level hold rule when promoting.
- Commits and PRs carry the attribution lines given by the session reminder.
- Do not use `pkill -f` / `pgrep -f` (it killed my own shell). Always `git fetch origin +main:refs/remotes/origin/main` before comparing with main. The GitHub GraphQL API is blocked from sessions: use `gh api` REST calls (create PRs with `gh api repos/.../pulls`).
- A new workflow file can only be dispatched after it is on main (or, if it already existed, from its branch).
- A Git branch named `perf` is impossible while `perf/species-index` exists; perf history lives on branch `perf-data`.
- The service worker fetches app/data from the network first, with app-shell fallback for offline navigations; map styles refresh from the network while tiles and media are cached first (up to 1,500 runtime resources). The phone may need two close-and-reopen cycles to show a new deploy.

## What exists (jobs and tools)
Manual workflows: data-about, data-photos, data-state(s), data-research (`place`: id, list or `next:N[:prefix]`), data-journeys, data-journeyresearch, data-names, data-sync, data-syncall, data-regen, data-promote, data-linktest, data-outlines, data-worldparks, data-speciesphotos, data-after-promote (automatic: a merged `data/promote-*` PR starts data-photos). Scheduled: data-photos (daily 12:17 UTC; one bounded round of up to 120 places), perf (nightly 08:17 UTC; opens the issue "Site got slower" when a metric is over 15% worse), status (daily 11:07 UTC; issue "Project status"). Deploy: pages.yml. CI: ci.yml (sharded).
- Perf test: `tests/perf/perf.mjs`; history and latest report on branch `perf-data` (`latest.md`, `history.json`). Phone profile = 4x CPU, 1.6 Mbps, 150 ms. In addition to page/map/tap medians, it reports observational p50/p95 readiness for cold/warm place and food-web routes, selected-species response time, and route resource classes; readiness samples do not raise regression warnings.
- Species photos: `photos/species.json` ({title: [thumbnail path, page name]}), made by data-speciesphotos; the app requests 120px Wikimedia thumbnail variants where available, lazily loads food-web SVG and journey photos, and resolves a place-specific wiki alias through its canonical species article or Latin name. Journey images load when Journeys opens (or a journey is opened directly); titles with no manifest match keep their placeholders. Titles with no picture are in `photos/species_missing.json`.
- Place photos: `photos/places/` + `places.json`. Outlines: `data/outlines/<id>.json` (PAD-US, then Wikidata/Commons, then OpenStreetMap; `bounds_more.py` drops a match whose box is far from the place).
- Size budgets in `build/budget.py` (index 3.6 MB, pilot 4.2, species 4, webs 25, outlines 20).
- Place pictures wait for the map (map drawn, a touch, 9 s, or a link to a place). Food-web species photos use smaller thumbnail variants and native lazy loading.
- After adding or promoting places run `python3 build/species.py pack`. A data branch that clashes with main only on `data/species.json` or `data-auto/order.json`: use data-sync.

## Waiting on the owner (last known)
- #148 two more park outlines (CI green); #141 world-parks candidate list (rerun with size-scaled quotas; review quotas, then choose which become stories).
- data-research `next:120` results, then draft stories in batches of about 40 (draft file, review file sent to him, PR only after his approval).
- A new data-photos PR may appear (about 129 places lacked a photo).
- First perf results after the picture hold: compare the new run with the first one (phone: map drawn 13.4 s, page loaded 5.7 s, 47 Wikipedia requests at start, state parks on 1.1 s, back taps 250 to 400 ms).
- His iPhone feedback on map speed.

## Parked ideas (not decided, do not start without asking)
- Scheduled story writing by the Claude API (needs an API key as a repo secret; costs money) and the chain research to draft. Parked on cost.
- Scheduling design chat: which jobs run on a schedule and in what order.
- What-if redesign; wording "places" vs "ecosystems".
- Real-device checks beyond the owner's iPhone.
- Deleting stale branches (his only; offer a list to approve). Candidates: perf/species-index and merged branches.
- Auto-sync of stale data branches after merges; skipping browser tests on data-only PRs (faster CI path).
- Step 3 of the speed work: lazy-load the 697 KB of state-park index data (risky: ties and "Also found in" use all places). Only if the phone is still slow.
- Desktop paging of cards; a static world silhouette while tiles load.
- Weekly report of dead links and places lacking a photo or outline.
- Journeys research: `research/journey-research.md` unread; journeys need real routes only.
- Umbagog Refuge stays out of promotion.
- Thin states: SD 4, OR 8, NE 8, NV 13 parks. 39 held parks with family-level link problems.
- About 124 places still have no outline (list on branch `data/outlines-report`); rerun data-outlines after new promotions.
- World national parks: choose candidates from #141 and turn them into places with stories.
- Sync tool improvements (syncmain.py).
