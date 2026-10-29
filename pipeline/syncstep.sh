#!/bin/bash
# syncstep.sh: bring the CURRENT branch (everything committed) up to date with main, with the shared-file rules of pipeline/syncmain.py,
# repack the species table and commit. Used by every data job just before it pushes, so its pull request opens already up to date,
# and by data-sync. Writes one line for the pull request to /tmp/sync.md. Exit 1 when a person has to look (the merge is undone first).
set -u
git config user.name "connected-earth-bot"; git config user.email "actions@users.noreply.github.com"
git fetch -q origin main
if git merge --no-edit origin/main >/tmp/sync.log 2>&1; then
  echo "Merged main without clashes." > /tmp/sync.md
else
  git show origin/main:pipeline/syncmain.py > /tmp/syncmain.py
  if ! SYNC_ROOT="$PWD" python3 /tmp/syncmain.py >>/tmp/sync.log 2>&1; then
    WHY=$(grep -m1 "need a person" /tmp/sync.log | cut -c1-600)
    git merge --abort 2>/dev/null || git reset -q --hard
    echo "**Not up to date with main:** ${WHY:-the merge failed}. Needs a person." > /tmp/sync.md
    cat /tmp/sync.md; exit 1
  fi
  echo "Brought up to date with main; shared-file clashes resolved by the sync rules:" > /tmp/sync.md
  grep -E "^(resolved|merged|promoted)" /tmp/sync.log | sed 's/^/- /' | cut -c1-300 >> /tmp/sync.md
fi
python3 build/species.py pack
git add -A -- data data-auto pipeline/names.json pipeline/state_queue.txt
git commit -qm "Repack species after bringing the branch up to date with main" || true
cat /tmp/sync.md
