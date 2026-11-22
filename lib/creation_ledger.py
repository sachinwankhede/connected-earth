#!/usr/bin/env python3
"""creation_ledger.py: the one writer of the refusal ledger (docs/ADD-SPECIES.md; the same record shape serves species, places and journeys, one file per kind).

A candidate that was refused (no licensed picture, no summary, a conflict) is written down here with the result of every step, so the list of refusals is the list of what to fix or which source to add next.
It is tried again after the hold (contracts.LEDGER_HOLD_DAYS). The file is data/ledger/<kind>.json, {key: {steps: {step: {result: found|missing|skipped, detail}}, reason, tried, hold_until, attempts}}, written through a temporary name and os.replace.
The key is the candidate's own (a Wikipedia title for a species). Nothing here knows what a species, a place or a journey is."""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contracts
from place_photos import _read, _write_json

RESULTS = ('found', 'missing', 'skipped')


def _day(now):
    if now is None: return datetime.date.today()
    return now.date() if isinstance(now, datetime.datetime) else now


class Ledger:
    def __init__(self, kind, root='.'):
        self.kind = kind; self.path = os.path.join(root, 'data', 'ledger', kind + '.json'); self.rows = _read(self.path)

    def get(self, key): return self.rows.get(key)

    def record(self, key, steps, reason, now=None):
        """Write down a refusal. `steps` is {step: {result, detail}}; every step that ran is in it. A second refusal of the same key counts an attempt."""
        if not reason: raise ValueError('a refusal needs a reason')
        if not steps: raise ValueError('a refusal needs the steps that ran')
        for name, s in steps.items():
            if s.get('result') not in RESULTS: raise ValueError('step %r: result %r is not one of %s' % (name, s.get('result'), RESULTS))
        day = _day(now)
        self.rows[key] = {'steps': {n: {k: v for k, v in s.items() if k in ('result', 'detail') and v is not None} for n, s in steps.items()},
                          'reason': reason, 'tried': day.isoformat(), 'hold_until': (day + datetime.timedelta(days=contracts.LEDGER_HOLD_DAYS)).isoformat(),
                          'attempts': int(self.rows.get(key, {}).get('attempts', 0)) + 1}

    def clear(self, key):
        """The candidate was added: it leaves the ledger."""
        self.rows.pop(key, None)

    def due(self, now=None):
        """Keys whose hold has ended, oldest first: the weekly retry takes these."""
        d = _day(now).isoformat()
        return sorted((k for k, r in self.rows.items() if r['hold_until'] <= d), key=lambda k: (self.rows[k]['hold_until'], k))

    def by_reason(self):
        """{reason: count}: how many refusals each reason caused (the priority list for the next source)."""
        out = {}
        for r in self.rows.values(): out[r['reason']] = out.get(r['reason'], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))

    def commit(self):
        if self.rows or os.path.exists(self.path): _write_json(self.path, self.rows, indent=1)
