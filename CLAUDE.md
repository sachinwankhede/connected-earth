# Connected Earth

- At the start of a session read `docs/STATE.md` (decisions, what exists, items waiting on the owner, parked ideas) and update it in the same pull request as any work that changes it.
- Before any UI work, read `docs/DESIGN.md` and follow it. If a request conflicts with a rule, point it out and update the rule rather than quietly breaking it.
- Build with `python3 build/build.py --all` (index.html, pilot/index.html, sw.js and api/ are built by CI and the deploy and are not committed; never hand-edit them). While iterating run only the fast local checks in "Testing on GitHub" below.
- Merging to main follows the tier policy in Ground rules (the agent merges data, UX, jobs/lib, and speed work after green checks; owner merges governance and workflows); deleting branches or previews is the owner's call.
- After any merge to main, read the result of the `deploy` run for that commit (`gh api repos/<repo>/actions/runs?head_sha=<sha>`, then its jobs) before reporting the merge as done. A cancelled run replaced by a newer merge is fine: read the newer one. If it failed, say so at once and open or fix it; the "Deploy failing" issue is opened by the `alert` job.

## Testing on GitHub (browser tests and perf runs never run in a session)
- Locally run only the build, `build/budget.py`, the validator and non-browser tests (Python and Node unit tests). Do not start a browser.
- CI (`checks`) runs on pull requests and on main, not on a plain branch push: open the pull request first, then read the `gate` check. If it is red, find the failing job (`app (n/3)`, `data` or `job scripts`) with `gh api repos/<repo>/commits/<sha>/check-runs`, then read its log (`gh api repos/<repo>/actions/jobs/<id>/logs`, look for `not ok`). Before changing code for a red check, see whether main fails the same test. Re-run failed jobs at most once (`gh api -X POST repos/<repo>/actions/runs/<id>/rerun-failed-jobs`).
- What runs depends on what changed (`build/ci_changes.py`): browser tests run for app changes only. Data pull requests run validation, the build, budgets and one smoke test; docs and job-state changes run nothing. A green data pull request does not prove the app tests pass. A single test cannot be run on GitHub: the app suite runs whole, in three shards.
- Pull requests opened by the data jobs wait for the owner to approve the workflow run (`action_required`), which counts as standing approval for the agent to merge once gate is green.
- Speed comparisons: push the branch, then dispatch `perf-ab` (`gh api -X POST repos/<repo>/actions/workflows/perf-ab.yml/dispatches -f ref=main -f inputs[ref_b]=<branch>`; optional `ref_a` default main, `nav` 1 to also time place opens, `runs` default 5). For app-code PRs (`app == true` in `build/ci_changes.py`), the agent dispatches `perf-ab` and reads the comparison table before merging; docs, data and jobs PRs skip it. It builds both sides on one machine, alternates the runs and comments the table on the pull request for B; only the A-versus-B difference is meaningful (flagging regressions > 15% for review). Runs for different branches may overlap (each gets its own machine). The live-site `perf` workflow runs one at a time (group `perf`); never compare its numbers with `perf-ab`'s.

## Ground rules
1. **Code and data are treated differently.** Agents (Claude & Gemini) manage code (branches, small pull requests, tests) and perform semantic inference. Data is managed by automated GitHub Actions jobs that open pull requests; agents do not hand-edit it or read the data folders.
2. **Merge Policy & Quality Tiers (Owner is not the review bottleneck).** Nothing merges by itself because "Allow auto-merge" is off; the agent merges qualifying pull requests once checks pass:
   - **The agent merges on a green `gate`:**
     - **Data pull requests:** opened by automated data jobs; every data pull request lists its sources and licences in the body, with the 10-item spot check required by `docs/PROMOTION.md`. Data job PRs need the owner to approve the workflow run (`action_required`) before `gate` can turn green; that approval counts as the standing approval.
     - **UX changes:** CSS, layout, cards, sheets, gestures, and UI rendering. The agent runs `perf-ab` before merging (informational; blocks only on >15% slowdown). After a UX merge, the agent reads the `deploy` run and posts it on the issue item. The owner checks on the live iPhone afterwards, and the item stays `status:waiting-owner` until verified. (Cloudflare edge previews remain available as an optional pre-merge preview tool).
     - **`jobs/` and `lib/` code:** requires a unit test in the pull request and must pass the allowed-sources check (`tests/jobs/allowed_sources_test.py`). All downloads route through `lib/fetch.py` which refuses unlisted hosts at run time.
     - **Docs-only changes:** documentation and markdown updates (except owner-merged governance files).
   - **The agent merges on green `gate` and `perf-ab`:**
     - **Speed & Latency App Code:** app changes affecting speed, bundle payload, or performance budgets (`app == true` in `build/ci_changes.py`, e.g. `src/app/data.js`, `build/build.py`, `build/pages_payload.py`, `sw.js`, or bundle chunking). The agent dispatches `perf-ab`, reads the comparison table, and merges if there is no regression > 15% (and > 20 ms / KB).
   - **Stays owner-merged:** `CLAUDE.md`, `docs/DESIGN.md`, `build/allowed_sources.json`, `tests/jobs/allowed_sources_test.py`, `lib/fetch.py`, and `.github/**` (workflows decide permissions, triggers, and secrets).
3. **Heavy work runs in GitHub jobs; agents write code and perform semantic inference.** Scheduled GitHub Actions perform all heavy web fetches, rate-limited downloads, and bulk staging. Agents write code (small branches, pull requests, tests) and perform semantic inference (summaries of at most 60 words, diet validity checks, taxonomic classification).
4. **Data workflow security & cost control.** No secrets in data workflows; keep `GITHUB_TOKEN` only. Any paid API key (for example Gemini) needs the owner's approval, and anything that costs money stays parked.
5. **Performance is critical for scaling.** First paint loads only what is necessary; detail loads on demand. Size budgets and perf budgets block regressions.
6. **Mobile-first iPhone standard.** The app shell and opened places work offline; search may be briefly unavailable after launch. Touch ergonomics and strict word budgets (story ≤ 60 words, why ≤ 40 words) are non-negotiable.
7. **Stop Conditions.** The agent stops and asks the owner only for:
   - Red CI it cannot root-cause
   - A licence doubt
   - A conflict with the spec
   - A `perf-ab` result more than 15% slower
   - Raising the first-view size budget (ask before editing `build/firstview.py`).

## Multi-Agent Collaboration Protocol (Claude & Gemini)
Multiple AI agents (Claude and Gemini) collaborate on this repository concurrently under the following rules:
- **No Direct Commits to `main`:** Every agent works on an isolated branch named `issue-<number>-<slug>` or `feat/<slug>`.
- **Task Locking via Agent Labels:** Because agents share the same GitHub token, an assignee tells you nothing. An agent claims a task atomically by applying its agent label (`agent:claude` or `agent:gemini`) alongside `status:doing` on the GitHub issue. The issue label is the lock; the entry in `docs/STATE.md` is only the log. Do not touch tasks or files actively claimed by the other agent.
- **Session Continuity:** Always read `docs/STATE.md` at the start of a session and update it with decisions, numbers, and PR status before ending.
- **Commit Attribution:** Keep the trailer your tool adds. Claude uses `Co-Authored-By: Claude <model> <noreply@anthropic.com>`.

## Items and status
- **The item is the outcome; a pull request is the means.** Every piece of work is one GitHub issue (title = the outcome) with a theme label (`theme:latency`, `theme:data`, `theme:photos`, `theme:process`) and, while open, a status label (`status:idea`, `status:doing`, `status:waiting-owner`). Closed = done. The body holds the goal, decisions and numbers.
- Every pull request says `Part of #N` or `Closes #N` in its body. When a PR merges or a job finishes, update the item (label, body, close it) in the same turn. Open a new item when a new topic comes up in conversation, not only when a PR is opened.
- `bash jobs/status.sh` and the issue "Project status" show items first (waiting on the owner, doing, not started, done), then the PRs with their item and any PR without one. REST only (`gh api`); GraphQL is blocked from sessions, so no Projects board.

## Keep the context small (do this first)
Most of this repo is data, not code. Never read, cat, grep -r or list whole data folders, and do not use Explore/"load the repo" style scans. A new session should read only `CLAUDE.md`, `docs/STATE.md`, the one doc for the task, and the specific files it will change.
- **Code (read when needed):** `src/app.html` (the page shell: head loaders, `__INCLUDE:app/<file>__` lines) and `src/app/*.js`, `src/app/style.css` (the app, one file per area, see `docs/ARCHITECTURE.md` "App source files"; read only the file and functions you change), `build/`, `jobs/*.py`, `tests/`, `.github/workflows/`, `docs/`.
- **Data (do not open; query one file or one key with a script):** `data/` (1,549 places in `data/places/`, of which 277 are pilot places marked `stage: pilot`), `data/species/species.json` (5,600 species), `data/outlines/`, `photos/` (41 MB of images plus `places.json`, `species.json`), `research/` (on the `research` branch), `jobs/reports/`, `jobs/*.json`.
- **Built or generated (never read or edit):** `index.html`, `pilot/index.html`, `sw.js`, `api/`, `node_modules/`.
- To answer a question about the data, run a short Python/`jq` command that prints only the counts or the few records needed; to see jobs and PRs use `bash jobs/status.sh` or the issue "Project status".
- Do not poll for job results in a loop in the main session; start a background wait and read only the final line.
- Prefer a fresh session per topic. Update `docs/STATE.md` before ending one.

## Data jobs and workflows
- Discuss the design before building a workflow or scheduled job. Run one job by hand first to judge quality and timing before choosing a schedule or order.
- Heavy web pulls run as GitHub Actions jobs, not from the sandbox. Trigger them and leave them in the background; work on other things meanwhile. Dispatch jobs that share a concurrency group one at a time (a pending run is replaced by the next).
- Jobs never merge on their own; they open one pull request. The agent merges data pull requests once `gate` is green (the owner's workflow approval `action_required` serves as standing approval).
- Every data pull request lists its sources and licences in the body, with the 10-item spot check that `docs/PROMOTION.md` requires.
- Data jobs use only external hosts and licences listed in `build/allowed_sources.json` (per source, e.g. Wikimedia and GBIF: CC0 and CC BY only). All downloads route through `lib/fetch.py`, which refuses unlisted hosts at run time. Adding a host or licence to `build/allowed_sources.json` requires owner approval.
- Batch sizes: about 15 places per story batch and 15 states per state batch. Stories are the part that needs the owner's review, so keep a batch within what he can read in one sitting.
- Content rules: story at most 60 words, why-it-matters at most 40; park summaries are one Wikipedia sentence; journeys only where the source text supports a real route.
- Promotion follows `docs/PROMOTION.md` (including the 60% family-level hold rule). Use the `data-promote` workflow; the 10-link spot check goes in the pull request.
- Shared lists are one file per job (species rows since #276, place order in `data/order/` and journeys one file each since #277), so data branches no longer clash on them; `data-sync` still brings a branch up to date when it clashes only on `jobs/names.json`, `jobs/state_queue.txt` or a place's food web. Run `python3 build/species.py pack` after adding or promoting places (it also moves new eating-link evidence into `data/diets/`, #256).
- `bash jobs/status.sh` shows open pull requests, running jobs, the state queue and finished research.
