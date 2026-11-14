# Using the Gemini API in Connected Earth

How we use Gemini for bulk drafting and classification, what limits apply, how the jobs loop through models and recover, and what we learned. Start here before building another Gemini job. Update this file in the same pull request as any change to the Gemini jobs or any new learning (the log at the end says what changed when). Origin: #747 (decision), #196 (first use: story drafts).

## Why Gemini, and the rules

- Bulk drafting runs on Gemini so it does not use the agent sessions' usage (owner, 13 Nov). Claude orchestrates and reviews; Gemini drafts.
- `CLAUDE.md` ground rule 4 allows the secret `GEMINI_API_KEY` only in manual (`workflow_dispatch`) workflows named `data-gemini-*`, run from `main`, never on `pull_request`. The secret goes as an environment variable to the one step that calls the API, never to the whole job. The call goes through `lib/fetch.py` (host `generativelanguage.googleapis.com` is listed in `lib/allowed_sources.json`). Every such workflow has a hard cap on rows and tokens per run. No other secret is added.
- The key is on the **free tier**. The owner sets any monthly cap at Google. Anything that costs money stays parked until the owner approves it.
- A draft is never written into a place or data file by the job. It goes to a branch (`gemini-stories`), the owner reads it and approves, and a separate step promotes the approved ones (`jobs/promote_stories.py`, #766).
- Run one task by hand and judge quality and token use before any schedule or full run.

## Free-tier limits (read from the owner's AI Studio usage screen, 13 Nov 2026)

Limits are per project and per model, in three kinds: requests per minute (RPM), tokens per minute (TPM, input) and requests per day (RPD). The daily count resets at midnight Pacific time (08:00 UTC in November). The numbers change; re-read the usage screen before a big run and update this table.

| Model | Requests per day | Per minute | Notes |
|---|---|---|---|
| gemini-3.5-flash-lite | 500 | 15 | first choice for bulk |
| gemini-3.1-flash-lite | 500 | 15 | second |
| gemini-3.8-flash | 20 | 5 | stronger, tiny daily allowance; last in the chain |
| Gemma 4 26B and 31B | 14,400 | 30 | 16K tokens a minute; not used yet (small context) |
| many other models | 0 or 20 | | not usable for bulk |

A retried 503 costs a request. One story draft costs about 6,500 prompt tokens and about 100 output tokens (13 places: 97,827 prompt and 1,919 output tokens). A 15-second gap between requests stays far inside the per-minute limits.

## Calling the API

- Endpoint `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`, key in the `x-goog-api-key` header (never in the URL, never printed or written).
- Ask for JSON: `responseMimeType: application/json` plus a `responseSchema`; `temperature` 0; a `maxOutputTokens` cap.
- Use only the source text: the system prompt says every fact, number and name must appear in the source and to leave out what is not supported.
- Ask for fewer words than the check allows (the story prompt asks for 50 and 34 words; the checks allow 60 and 40), so a draft that runs long still passes.
- Record with every result: the model that wrote it, the prompt version (`PROMPT_VERSION`, for example `stories-2`), the token counts and the time.

## Error model and the loop through models

Defined in `jobs/gemini_stories.py` (now in `lib/gemini_api.py`, see "Reuse"):

- **429, quota:** if Google gives a retry delay up to `MAX_WAIT` (90 s) the job waits once and tries again; otherwise that model is **out for the run** (a daily limit can give a delay of hours).
- **500, 503, 504 and timeouts ("high demand"):** retried after 30, 90 and 180 seconds (`BUSY_WAITS`); if the place stays busy the model is marked out (`Overloaded`). The first run lost 13 minutes to 503s before this existed.
- **Model chain:** the `model` input (workflow) or `GEMINI_MODEL` is a comma list tried in order, from an allowlist (`MODELS`); an unknown name is refused. When a model is out, the next model takes over the same place. The run stops cleanly (exit 0) only when every model is out, and says `STOP: every model is out`.
- **Pacing:** one request at a time, at least `GAP` (15 s) apart.
- **Stopping is safe:** each draft is its own file, written the moment it is checked (accepted, or `rejected/<id>.json` with the reason); the workflow's save step pushes the branch even after a stop or failure; the next run carries on where this one stopped. A rejected place is not asked again unless the run has `again`.
- Default chain: `gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash`. The cheap 500-a-day models go first so a bulk run fits in one day.

## Checks on a draft (stories)

Story at most 60 words, why at most 40; every number in the draft appears in the research text; every capitalised word that does not start a sentence appears in the research text; no coordinates (the prompt forbids them). Known false alarms: a compound such as "Chinese-North" and a number written "720,000" versus "720.000". Rejections are kept with their reason, so a human can accept or retry them. Checking numbers and names against the source is what keeps invented facts out; keep an equivalent check in any new task.

Results so far: first good run 13 of 15 accepted; the full run 112 accepted and 8 rejected of 120; a retry of the 8 accepted 3.

## Lessons from the trial (journey months, `data-gemini-trial`)

The key, host, model and JSON output work. Quality on five journeys: 3 usable; the monarch got all 12 months (defensible but not useful); the caribou got an empty list although the text names spring and autumn; the altiplano flamingo was empty because its text names no season. The validators passed all five, so before using Gemini for months: define the season months in the prompt (spring 3 to 5, and so on), and add a check that flags an empty answer whose `basis` names a season. A validator that only checks the shape is not enough.

## Adding another use case (checklist)

1. Name the task and its input rows; say what a wrong answer costs and who checks it.
2. Write the prompt with the source text only; add the schema; choose word and format limits that the checks enforce.
3. Write checks that compare the answer to the source (numbers, names, allowed values), not only its shape.
4. One file per result, written as soon as it is checked; rejected results kept with a reason; results go to a branch or a data pull request, never straight into data.
5. A manual `data-gemini-<task>` workflow: `workflow_dispatch`, `main` only, secret on the one step, `limit` input with a hard maximum, the model chain input, a save step that runs even after a stop.
6. A unit test with a fake API for the loop, the retries, the quota stop and every check.
7. Run 10 to 15 rows, read every result, then decide the full run; record the numbers in this file.

## Reuse: `lib/gemini_api.py`

The shared calling code lives in `lib/gemini_api.py` (#772): `generate()` (one request with the 429 and busy handling above), `Chain` (the model list and hand-over), `request_body()` (system prompt, user text, JSON schema, temperature, token cap), `retry_delay()`, the errors `QuotaStop` and `Overloaded`, and the constants `GAP`, `MAX_WAIT`, `BUSY_WAITS`, `MAX_BUSY_IN_A_ROW`. `jobs/gemini_stories.py` and the trial `jobs/gemini_batch.py` use it. A new task writes only its prompt, schema, checks and the loop over its rows (see the story job's `main()` for the pattern: pace with `GAP`, `except QuotaStop` and `except Overloaded` call `chain.out(...)`). The module's tests are in `tests/jobs/gemini_stories_test.py` until `ci.yml` (owner-merged) lists a file of their own.

## Pipeline pattern for batch tasks (owner decisions, 13 Nov: generic runner, manual button first, judge plus sample)

Every Gemini task has the same stages: choose the items, gather source text, draft, deterministic checks, judge, human review, merge, report (#779 builds this for stories first).
- **Task specs and one runner.** A task is a spec in `jobs/` (item selector, source, prompt, schema, checks, judge rubric, writer into a data file). One generic manual workflow runs a spec by name; the caps (rows, tokens, time) are fixed in the workflow so a spec cannot raise them. The workflow is owner-merged once; a new use case is an agent-merged spec with tests and the allowed-sources check. Journeys months is the second task, to prove the pattern.
- **Files are the interface.** Each stage reads and writes one file per item on a branch and is safe to re-run; state lives in the repository, not in a session.
- **Review.** Deterministic checks first, then a judge from a different model (it flags or rejects, never edits: unsupported claims, wording unsuited to children, near-duplicates), then a data pull request per batch (about 25 items) carrying the judge's verdicts. Claude reads only what the judge flags (at most 5 a batch); the owner glances at a 5-item sample until the judge proves reliable, then the sample stops. The owner's merge is the approval.
- **Throttle.** The pipeline refuses to start while an unreviewed batch pull request is open, so the owner's review pace is the speed limit and no quota is spent on drafts nobody will read.
- **Trigger.** Manual button first (ground rule 4 allows Gemini workflows only by `workflow_dispatch` from `main`). After a few clean batches decide between a scheduled routine of the agent that dispatches it (keeps rule 4, a little session usage) and an owner amendment of rule 4 for a capped GitHub schedule for approved specs (no session usage).
- **State.** Counts that change (drafted, judged, awaiting review, merged) are computed by `jobs/status.sh` and reported in each batch pull request, not written by hand into `docs/STATE.md`, which keeps decisions and learnings.
- **Source text is untrusted.** The model has no tools and returns JSON only; a poisoned source can at worst produce a bad draft, which the checks, the judge and the review catch.

## Other free AI providers (owner, 13 Nov: "there are other free AI key providers too, which we can add later")

Gemini is the first provider, not the only one. Keep this in mind when designing: the task side (prompts, schemas, checks, one file per result, the review pages) must not depend on Gemini, and a second provider is welcome, for example as the judge of the story pipeline (#779), where a different model family makes a more independent reviewer.
When one is added (each needs the owner's approval first, because `CLAUDE.md` ground rule 4 names only `GEMINI_API_KEY`):
1. its host and licence line go into `lib/allowed_sources.json` (owner-merged); its key is a repository secret used only by a manual `data-<provider>-*` workflow, on the one step that calls it, with caps per run, as for Gemini;
2. read its free-tier limits (requests per minute and per day, tokens, reset time) and its terms, including whether free-tier prompts are used for training (our inputs are public Wikipedia text, but check), and add a limits table to its own section here;
3. only then generalise: move the shared pieces (`Chain`, the error model, `request_body`) behind a small provider interface (for example a `lib/llm.py` with one adapter per provider, `lib/gemini_api.py` staying the Gemini adapter). Do not build the interface before the second provider exists.

## Where things are

- Shared code: `lib/gemini_api.py`.
- Jobs: `jobs/gemini_stories.py` (stories), `jobs/gemini_batch.py` (trial), `jobs/promote_stories.py` (copies approved drafts into place files).
- Workflows: `data-gemini-stories`, `data-gemini-trial`.
- Tests: `tests/jobs/gemini_stories_test.py`, `tests/jobs/gemini_batch_test.py`, `tests/jobs/promote_stories_test.py`.
- Drafts: branch `gemini-stories` (`REVIEW.md` and `REVIEW-NN.md` index them). Research text: branch `research`.

## Log

- 13 Nov 2026: decision and trial (#747); first story runs failed on 503 and a daily limit; retry, early stop (#756) and the model chain (#758) added; stories prompt `stories-2` (#759); 112 drafts promoted (#766). This guide written.
- 13 Nov 2026: calling code moved into `lib/gemini_api.py` (#772); the story job behaves as before (its 19 tests pass unchanged), the trial uses it without busy retries.
- 13 Nov 2026: section on other free providers added (owner note); nothing built for them yet.
- 13 Nov 2026: pipeline pattern decided (generic runner, manual button, judge plus sample); built under #779.

## Provider interface (`lib/llm.py`, #779 step a)
A task calls `llm.complete(provider, chain, system, text, schema, key)` instead of `gemini_api` directly. `llm.get('gemini')` is the adapter over `lib/gemini_api.py` (which keeps the HTTP, retry and quota code); another provider is one `Provider` subclass plus `llm.register()`, with its host in `lib/allowed_sources.json` and its calls through `lib/fetch.py` (both owner-merged). `complete()` returns the answer with the model that gave it, drops a model that is out of quota (or busy for `MAX_BUSY_IN_A_ROW` items in a row) and hands the same item to the next, and says `no model left` when the chain is used up. `QuotaStop` and `Overloaded` are the `gemini_api` classes. Existing jobs are unchanged; moving them onto `llm` is the next step. Tests: `LlmInterfaceTests` in `tests/jobs/gemini_stories_test.py`.

## Generic runner (`jobs/ai_task.py`, workflow `data-gemini-task`, #779 step a)
One loop for every model task: `python3 jobs/ai_task.py <task> <input dir> <out dir> [limit] [--again]`. A task is a `Task` (system prompt, schema, `prompt_version`, `items()`, `check()`, `review()`); the runner lists what is left, asks through `lib/llm.py` and its model chain, waits `GAP` between requests, checks each answer, writes it to `<out>/<id>.json` or `<out>/rejected/<id>.json` the moment it is checked, and stops cleanly when every model is out of quota, so every run resumes. `stories` is the first task and wraps the prompt, checks and review pages in `jobs/gemini_stories.py` (unchanged; it stays the reference and the old workflow `data-gemini-stories` stays until `data-gemini-task` has done one batch). Journey months are the second task (a later step). The workflow `data-gemini-task` takes `task` (a choice), `limit`, `model` and `again`, commits to the branch `gemini-<task>`, and keeps every rule of the stories workflow (manual only, from main, the key only on the one step that calls the API, no pull request, no place file changed). Tests: `AiTaskRunnerTests` in `tests/jobs/gemini_stories_test.py`.

## The judge (`judge` task in `jobs/ai_task.py`, #779 step b)
`python3 jobs/ai_task.py judge <research dir> <drafts dir>` reads each accepted story draft (`<drafts dir>/<id>.json`) with its research text and asks a second model whether it can be published as it is. It flags or passes and never edits. Rubric (in `JUDGE_SYSTEM`): a claim, number, name or date the source does not support; wording unsuited to children (frightening or graphic detail, adult themes, marketing words, opinions as facts); anything confusing or wrong. The source text is treated as data. A pass goes to `judge/<id>.json`, a flag to `judge/rejected/<id>.json` with the problems; `JUDGE-FLAGGED.md` lists only the flagged ones, which is all Claude reads (at most 5 a batch). Near-duplicates among the drafts are flagged by a plain 3-word-shingle comparison (Jaccard 0.5), not by the model. The default models (`gemini-3.1-flash-lite`, `gemini-3.8-flash`) skip the writer's first model; each record keeps `writer_model`. It writes into the same branch as the drafts (`gemini-stories`), so one run of the judge follows one run of the writer. `python3 jobs/ai_task.py --branch <task>` prints a task's branch (an unknown task exits 2), so the workflow needs no list of tasks. Limits: writer and judge share the research text, so an error in the source passes. Tests: `JudgeTaskTests`.

## The batch builder (`jobs/story_batch.py`, #779 step c)
`python3 jobs/story_batch.py <drafts dir> [--data data/places] [--n 25] [--body batch-body.md]` takes the first N drafts (id order) that the judge passed, whose place file exists and has no story, writes them into the place files (through `promote_stories.promote`; the diff is the review, merging is the approval) and writes the pull request body: counts, the table of what is in, what the judge flagged and why (those are not in the batch), the sources and licences line, and the 10-item spot check (ten evenly spaced stories to read against their research text, as `docs/PROMOTION.md` requires). Drafts the judge has not read, the ones it flagged and the ones the checks rejected stay out. Exit 3 and no change when nothing qualifies. No model call, no fetch. A workflow that runs it and opens the pull request (and refuses to start while a batch pull request is open) is the next, owner-merged, piece. Tests: `StoryBatchTests`.
