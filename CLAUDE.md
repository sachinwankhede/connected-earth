# Connected Earth

- At the start of a session read `docs/STATE.md` (decisions, what exists, items waiting on the owner, parked ideas) and update it in the same pull request as any work that changes it.
- Before any UI work, read `docs/DESIGN.md` and follow it. If a request conflicts with a rule, point it out and update the rule rather than quietly breaking it.
- Build with `python3 build/build.py --all` (index.html, pilot/index.html, sw.js and webs/ are built by CI and the deploy and are not committed; never hand-edit them). Test only the affected area while iterating; the full suite runs in CI before merging to main.
- Merging to main and deleting branches or previews is the owner's call; ask first.

## Ground rules
1. **Code and data are treated differently.** Claude manages code (branches, small pull requests, tests). Data is managed by GitHub jobs that open pull requests; Claude does not hand-edit it or read the data folders. The owner merges.
2. **Performance is critical for scaling.** That needs (a) correct data modelling: only what the first paint needs is loaded up front, detail loads on demand, and no file is written by two jobs at once; (b) a way to measure: `tests/perf`, same workflow and profile, no overlapping runs; (c) safe experiments: one change per pull request, measured before and after on the same profile, easy to revert, merged only by the owner. Size budgets already block a pull request; perf budgets are planned.
3. **GitHub does the heavy work.** Web pulls, builds, perf runs and A/B comparisons run as Actions jobs, in parallel whenever they share neither a concurrency group nor a file. Claude does the inference and the small code changes, and keeps sessions small; continuity lives in this file and `docs/STATE.md`.
4. **The owner's iPhone is the final check;** synthetic numbers only guide. Offline and install behaviour are constraints, not afterthoughts. The owner's review time is the scarce resource, so batches stay readable. Decisions are written down in the repo.

## Keep the context small (do this first)
Most of this repo is data, not code. Never read, cat, grep -r or list whole data folders, and do not use Explore/"load the repo" style scans. A new session should read only `CLAUDE.md`, `docs/STATE.md`, the one doc for the task, and the specific files it will change.
- **Code (read when needed):** `src/app.html` (the app; read only the functions you change, use grep with line ranges), `build/`, `pipeline/*.py`, `tests/`, `.github/workflows/`, `docs/`.
- **Data (do not open; query one file or one key with a script):** `data/` (1,275 places, 25 MB), `data-auto/` (pilot, 278 places), `data/species.json` (5,600 species), `data/outlines/`, `photos/` (41 MB of images plus `places.json`, `species.json`), `research/` (on the `research` branch), `pipeline/reports/`, `pipeline/*.json`.
- **Built or generated (never read or edit):** `index.html`, `pilot/index.html`, `sw.js`, `webs/`, `node_modules/`.
- To answer a question about the data, run a short Python/`jq` command that prints only the counts or the few records needed; to see jobs and PRs use `bash pipeline/status.sh` or the issue "Project status".
- Do not poll for job results in a loop in the main session; start a background wait and read only the final line.
- Prefer a fresh session per topic. Update `docs/STATE.md` before ending one.

## Data jobs and workflows
- Discuss the design before building a workflow or scheduled job. Run one job by hand first to judge quality and timing before choosing a schedule or order.
- Heavy web pulls run as GitHub Actions jobs, not from the sandbox. Trigger them and leave them in the background; work on other things meanwhile. Dispatch jobs that share a concurrency group one at a time (a pending run is replaced by the next).
- Jobs never merge. They open one pull request; the owner merges. Approvals may be given per pull request ("yes to 71").
- Batch sizes: about 15 places per story batch and 15 states per state batch. Stories are the part that needs the owner's review, so keep a batch within what he can read in one sitting.
- Content rules: story at most 60 words, why-it-matters at most 40; park summaries are one Wikipedia sentence; journeys only where the source text supports a real route.
- Promotion follows `docs/PROMOTION.md` (including the 60% family-level hold rule). Use the `data-promote` workflow; the 10-link spot check goes in the pull request.
- A data branch that clashes with main only on `data/species.json` or `data-auto/order.json` is brought up to date with the `data-sync` workflow. Run `python3 build/species.py pack` after adding or promoting places.
- `bash pipeline/status.sh` shows open pull requests, running jobs, the state queue and finished research.
