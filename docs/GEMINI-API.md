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

Defined in `jobs/gemini_stories.py` (to be shared, see "Reuse"):

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

## Reuse (planned)

The calling code (key header, retry and busy handling, the quota stop, the model chain, pacing, token counts) lives inside `jobs/gemini_stories.py`, and the trial has its own copy in `jobs/gemini_batch.py`. Item #772 moves it into `lib/gemini_api.py` so a new task writes only its prompt, schema and checks.

## Where things are

- Jobs: `jobs/gemini_stories.py` (stories), `jobs/gemini_batch.py` (trial), `jobs/promote_stories.py` (copies approved drafts into place files).
- Workflows: `data-gemini-stories`, `data-gemini-trial`.
- Tests: `tests/jobs/gemini_stories_test.py`, `tests/jobs/gemini_batch_test.py`, `tests/jobs/promote_stories_test.py`.
- Drafts: branch `gemini-stories` (`REVIEW.md` and `REVIEW-NN.md` index them). Research text: branch `research`.

## Log

- 13 Nov 2026: decision and trial (#747); first story runs failed on 503 and a daily limit; retry, early stop (#756) and the model chain (#758) added; stories prompt `stories-2` (#759); 112 drafts promoted (#766). This guide written.
