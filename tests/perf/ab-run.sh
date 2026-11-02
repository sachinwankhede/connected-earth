#!/usr/bin/env bash
# ab-run.sh: measures two servers (A and B) one run at a time, alternating which goes first, so slow drift on the machine hits both sides alike.
#   bash tests/perf/ab-run.sh <runs> <out dir> <url A> <url B>
# Writes <out>/a/run-N.json and <out>/b/run-N.json (one perf.mjs run each); compare.mjs reads them.
set -u
RUNS=${1:?runs}; OUT=${2:?out dir}; URLA=${3:?url A}; URLB=${4:?url B}
mkdir -p "$OUT/a" "$OUT/b"
export PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1   # lets the returning-visit section see the worker's own fetch of the page
for i in $(seq 1 "$RUNS"); do
  if [ $((i % 2)) -eq 1 ]; then ORDER="a b"; else ORDER="b a"; fi
  for s in $ORDER; do
    if [ "$s" = a ]; then URL=$URLA; else URL=$URLB; fi
    echo "run $i side $s ($URL)"
    node tests/perf/perf.mjs --url "$URL" --runs 1 --nav "${NAV:-0}" --out "$OUT/$s/run-$i.json" --md "$OUT/$s/run-$i.md" > "$OUT/$s/run-$i.log" 2>&1 \
      || echo "  run $i side $s failed; see $OUT/$s/run-$i.log"
    grep -A40 "^PICTURES" "$OUT/$s/run-$i.log" | sed "s/^/  [$s] /" || true
  done
done
