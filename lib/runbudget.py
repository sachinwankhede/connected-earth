"""runbudget.py: the time budget and the resume line shared by the picture jobs (#1183).

A job that must check every missing item (species, places, journeys, nodes) cannot do it in one run, so each run has a time budget (`--minutes N`, 0 = none) and stops cleanly at the next item boundary, keeping what it found.
The resume contract (the workflow that chains runs reads it):
  - the job prints one line `more: N`: N = items still due and not tried by this run (0 = everything is checked);
  - exit 0: finished, nothing more due; exit 3: stopped by the time or size budget with N > 0 items still due, run again; exit 2: a source stopped the run (throttled, refused), do NOT chain; exit 1: error.
  - 'due' means: no picture, the source applies, and the source's own hold (30 days, lib/contracts.json, per-source tried ledger) has expired. A tried item is written to the ledger, so the next run does not offer it again; the order is fixed (input order, or sorted ids), so a run always continues where the last stopped.
  - an item that failed transiently (a download that failed) is recorded nowhere and is NOT counted in N within the same run, and every run tries at least one item before it can stop, so a chain makes progress."""
import time

EXIT_MORE = 3

class Budget:
    """minutes: None or 0 = no limit. clock is injectable for tests (read once at start and once per `late()` call)."""
    def __init__(self, minutes=None, clock=time.monotonic):
        self.minutes = minutes; self.clock = clock
        self.deadline = None if not minutes else clock() + minutes * 60
    def late(self): return self.deadline is not None and self.clock() >= self.deadline

def more_line(n): return 'more: %d' % n

def exit_code(stopped, more):
    """2 when a source stopped the run (never chain), 3 when more is still due, else 0."""
    return 2 if stopped else (EXIT_MORE if more else 0)
