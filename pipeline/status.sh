#!/usr/bin/env bash
# status.sh: what is open, what is running, what is queued. Needs the gh CLI. Usage: bash pipeline/status.sh
R=${REPO:-sachinwankhede/connected-earth}
# Items first: one issue per item (an outcome), a theme label (theme:*) and a status label (status:*). A pull request is the means, not the item.
echo "== Items (open issues; closed means done)"
for st in waiting-owner doing idea; do
  case $st in waiting-owner) h="WAITING ON YOU";; doing) h="DOING";; idea) h="NOT STARTED";; esac
  echo "-- $h"
  gh api "repos/$R/issues?state=open&labels=status:$st&per_page=100" --jq '.[]|select(.pull_request|not)|"* \(.title)  [\([.labels[].name|select(startswith("theme:"))|sub("theme:";"")]|join(","))]  (#\(.number))\n" + ([.body // ""|split("\n")[]|select(test("^\\*\\*(What I need from you|Status|Running now|Done|Next|Expected gain):"))|"    "+gsub("\\*\\*";"")]|join("\n"))'
done
echo; echo "-- DONE (closed, last 8)"
gh api "repos/$R/issues?state=closed&per_page=8&sort=updated" --jq '.[]|select(.pull_request|not)|select([.labels[].name|startswith("theme:")]|any)|"  #\(.number) \(.title)"'
echo; echo "== Open pull requests (each should say Part of #N or Closes #N; NONE means open an item)"
for n in $(gh api "repos/$R/pulls?state=open" --jq '.[].number'); do
  t=$(gh api repos/$R/pulls/$n --jq '"#\(.number) \(.title) [\(.head.ref)] \(.mergeable_state)"')
  sha=$(gh api repos/$R/pulls/$n --jq .head.sha)
  c=$(gh api repos/$R/commits/$sha/check-runs --jq '[.check_runs[]|(.conclusion // .status)]|if length==0 then "no checks" else (group_by(.)|map("\(.[0]) x\(length)")|join(", ")) end')
  ms=$(gh api repos/$R/pulls/$n --jq .mergeable_state)
  case "$c" in *failure*) v="CI RED";; *in_progress*|*queued*|*pending*) v="CI running";; *) if [ "$ms" = "dirty" ]; then v="NEEDS SYNC"; else v="READY"; fi;; esac
  it=$(gh api repos/$R/pulls/$n --jq '[.body // ""|scan("(?:Part of|Closes|Fixes) #[0-9]+")]|join(", ")')
  echo "$v  $t  | CI: $c  | item: ${it:-NONE}"
done
echo; echo "== Running or waiting jobs"
for s in in_progress queued; do gh api "repos/$R/actions/runs?status=$s" --jq '.workflow_runs[]|"\(.status)  \(.name)  \(.head_branch)  since \(.run_started_at)"'; done
echo; echo "== State queue (first 15)"; gh api "repos/$R/contents/pipeline/state_queue.txt?ref=main" --jq .content | base64 -d | head -15 | tr '\n' ' '; echo
echo; echo "== Research on the research branch"; gh api "repos/$R/contents/research?ref=research" --jq '.[].name' 2>/dev/null | sed 's/\.md$//' | tr '\n' ' '; echo
