# Connected Earth

- Before any UI work, read `docs/DESIGN.md` and follow it. If a request conflicts with a rule, point it out and update the rule rather than quietly breaking it.
- Build with `python3 build/build.py --all` (index.html, pilot/index.html, sw.js and webs/ are built by CI and the deploy and are not committed; never hand-edit them). Test only the affected area while iterating; the full suite runs in CI before merging to main.
- Merging to main and deleting branches or previews is the owner's call; ask first.

## Data jobs and workflows
- Discuss the design before building a workflow or scheduled job. Run one job by hand first to judge quality and timing before choosing a schedule or order.
- Heavy web pulls run as GitHub Actions jobs, not from the sandbox. Trigger them and leave them in the background; work on other things meanwhile. Dispatch jobs that share a concurrency group one at a time (a pending run is replaced by the next).
- Jobs never merge. They open one pull request; the owner merges. Approvals may be given per pull request ("yes to 71").
- Batch sizes: about 15 places per story batch and 15 states per state batch. Stories are the part that needs the owner's review, so keep a batch within what he can read in one sitting.
- Content rules: story at most 60 words, why-it-matters at most 40; park summaries are one Wikipedia sentence; journeys only where the source text supports a real route.
- Promotion follows `docs/PROMOTION.md` (including the 60% family-level hold rule). Use the `data-promote` workflow; the 10-link spot check goes in the pull request.
- A data branch that clashes with main only on `data/species.json` or `data-auto/order.json` is brought up to date with the `data-sync` workflow. Run `python3 build/species.py pack` after adding or promoting places.
- `bash pipeline/status.sh` shows open pull requests, running jobs, the state queue and finished research.
