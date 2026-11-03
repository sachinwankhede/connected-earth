#!/usr/bin/env python3
"""ci_changes.py: decide which CI checks a change needs. Reads changed file paths on stdin (one per line) and prints
app=true|false, data=true|false, jobs=true|false (GitHub output lines).
  app  : the app itself changed (src, build, app tests, fonts, package files, root files, the pages workflow): everything runs.
  data : only data changed (data, photos, data tests) or the checks or deploy workflow itself (ci.yml, pages.yml): validation, pack check, build, size budgets, data tests, one smoke test. A ci.yml or pages.yml change gets this lighter run (the build steps run, the browser suite does not).
  jobs : a job script or shared lib changed (jobs/*.py, jobs/*.sh, lib, job tests, state/promote tools, this classifier): the job self-tests only.
  quiet files (docs, notes, the data-job workflows, job state files such as queue, names, reports, park lists) run nothing.
Anything not listed counts as app, so a new kind of file is never skipped by mistake."""
import fnmatch, sys

QUIET = ['docs/*', '*.md', '.github/workflows/data-*.yml', '.github/workflows/status.yml', '.github/branches-to-delete.txt',
         'jobs/state_queue.txt', 'jobs/names.json', 'jobs/reports/*', 'jobs/nps/*', 'jobs/work/*']
JOBS = ['jobs/*.py', 'jobs/*.sh', 'lib/*', 'tests/jobs/*', 'build/state.py', 'build/promote.py', 'build/promote_check.py', 'build/ci_changes.py']
DATA = ['data/*', 'photos/*', 'tests/data/*', 'build/data_quality.py', 'lib/photo_registry.py', '.github/workflows/ci.yml', '.github/workflows/pages.yml']

def match(path, patterns):
    return any(fnmatch.fnmatch(path, p) for p in patterns)

def classify(paths):
    app = data = jobs = False
    for p in paths:
        p = p.strip()
        if not p or match(p, QUIET): continue
        hit = False
        if match(p, JOBS): jobs = hit = True
        if match(p, DATA): data = hit = True
        if not hit: app = True
    return app, data, jobs

if __name__ == '__main__':
    a, d, j = classify(sys.stdin.read().splitlines())
    for k, v in (('app', a), ('data', d), ('jobs', j)): print('%s=%s' % (k, 'true' if v else 'false'))
