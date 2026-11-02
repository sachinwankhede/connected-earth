#!/usr/bin/env python3
"""statesummary.py summary.tsv logdir budget.log: one table for the data-states pull request, one row per state.
Reads each state's log: parks built, how many pass the promotion floors and how many are held (and why, counted), duplicates dropped,
parks skipped, and outlines missing. Prints markdown."""
import collections, os, re, sys
summ, logs, budget = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ''
rows = []; failed = []
LABEL = {'family-level': 'mostly family-level links', 'links': 'too few links', 'species': 'too few species', 'plants': 'too few plants'}
for line in open(summ):
    st, status = line.split()[:2]
    t = open(os.path.join(logs, st + '.log'), errors='replace').read() if os.path.exists(os.path.join(logs, st + '.log')) else ''
    m = re.search(r'(\d+) places for %s: (\d+) pass the promotion floors; (\d+) held: (.*)' % st, t)
    why = collections.Counter()
    if m:
        for r in re.findall(r"\[([^\]]*)\]", m.group(4)):
            for w in re.findall(r"'([a-z\- ]+?) ", r): why[w.strip()] += 1
    miss = len(re.findall(r'^none %s' % st.lower(), t, re.M)); dup = len(re.findall(r'^dropped duplicate', t, re.M)); skip = len(re.findall(r'^skipped ', t, re.M))
    if status != 'ok':
        rows.append('| %s | FAILED | | | | | | |' % st); failed.append((st, t.strip().splitlines()[-25:])); continue
    rows.append('| %s | %s | %s | %s | %s | %d | %d | %d |' % (st, m.group(1) if m else '?', m.group(2) if m else '?', m.group(3) if m else '?',
                ', '.join('%s %d' % (LABEL.get(k, k), n) for k, n in why.most_common()) or '-', dup, skip, miss))
print('Automatic batch from the data-states workflow: the largest state parks of each state, added to the pilot (data-auto). Not shown in the main app until promoted.\n')
print('| State | Parks | Pass | Held | Held for (parks) | Duplicates dropped | Skipped (no outline from PAD-US) | Missing map outlines |\n|---|---|---|---|---|---|---|---|')
print('\n'.join(rows))
if budget and os.path.exists(budget): print('\nSize budget:\n```\n' + open(budget).read() + '```')
for st, tail in failed:
    print('\n<details><summary>%s failed: last lines of its log</summary>\n\n```\n%s\n```\n\n</details>' % (st, '\n'.join(tail)[-3000:]))
