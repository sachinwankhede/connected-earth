#!/usr/bin/env bash
# status.sh: what is open, what is running, what is queued. Needs the gh CLI. Usage: bash pipeline/status.sh
R=${REPO:-sachinwankhede/connected-earth}
echo "== Open pull requests"
for n in $(gh api "repos/$R/pulls?state=open" --jq '.[].number'); do
  t=$(gh api repos/$R/pulls/$n --jq '"#\(.number) \(.title) [\(.head.ref)] \(.mergeable_state)"')
  sha=$(gh api repos/$R/pulls/$n --jq .head.sha)
  c=$(gh api repos/$R/commits/$sha/check-runs --jq '[.check_runs[]|(.conclusion // .status)]|if length==0 then "no checks" else (group_by(.)|map("\(.[0]) x\(length)")|join(", ")) end')
  echo "$t  | CI: $c"
done
echo; echo "== Running or waiting jobs"
for s in in_progress queued; do gh api "repos/$R/actions/runs?status=$s" --jq '.workflow_runs[]|"\(.status)  \(.name)  \(.head_branch)  since \(.run_started_at)"'; done
echo; echo "== State queue (first 15)"; gh api "repos/$R/contents/pipeline/state_queue.txt?ref=main" --jq .content | base64 -d | head -15 | tr '\n' ' '; echo
echo; echo "== Research on the research branch"; gh api "repos/$R/contents/research?ref=research" --jq '.[].name' 2>/dev/null | sed 's/\.md$//' | tr '\n' ' '; echo
