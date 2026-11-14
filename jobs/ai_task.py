#!/usr/bin/env python3
"""ai_task.py: the generic runner for the manual data-gemini-* pipeline (#779 step a). One loop for every model task; a task is a small object (see Task) that says what to ask, what to check and how to list the drafts.
Usage: ai_task.py <task> <input dir> <out dir> [limit] [--again]     tasks: stories (the first one; journey months are the second, a later step)
What the runner does for any task: lists the items the task wants drafted (and skips those already in <out dir>), asks the model through lib/llm.py (a model chain: the next model takes over when one is out of quota or
stays busy), at least GAP seconds between requests, checks each answer with the task's own check, and writes it the moment it is checked: <out dir>/<id>.json (accepted) or <out dir>/rejected/<id>.json (with the reason).
So a stop or a failure loses nothing and the next run resumes. `limit` items per run (default 15; 0 = every item left; never more than MAX_ROWS). When every model is out the run stops cleanly (exit 0).
Models come from GEMINI_MODEL (a comma list, the provider's allowlist applies) and the key from GEMINI_API_KEY (sent only in a header by lib/gemini_api.py, never printed or written). The drafts are drafts: no place file is changed.
A new task: write a Task (name, system prompt, schema, prompt_version, items(), check(), review()) in this file or its own module and add it to TASKS; the runner, the workflow and the model chain need no change."""
import sys, os, json, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, HERE)
import llm

MAX_ROWS = 150; GAP = llm.gemini_api.GAP
class Item:
    """One thing to draft: id (the file name), name (for people), text (what the model is shown), source (what the check compares against)."""
    def __init__(self, id, name, text, source): self.id, self.name, self.text, self.source = id, name, text, source

class Task:
    name = ''; provider = 'gemini'; system = ''; schema = {}; prompt_version = ''; temperature = 0.2; max_out = 600
    def items(self, in_dir, out_dir, again): raise NotImplementedError   # the items still to draft, in a fixed order
    def check(self, answer, source): return None                          # None when usable, else the reason it is rejected
    def review(self, out_dir): pass                                       # write the files a person reads (optional)

def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.tmp'
    json.dump(obj, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, path)   # written whole, then moved into place

def run(task, in_dir, out_dir, limit, again, chain, key, provider=None, gap=GAP, log=print, sleep=time.sleep, clock=time.time):
    """The loop. Returns {'accepted', 'rejected', 'skipped', 'stopped', 'tokens_in', 'tokens_out'}; 'stopped' is True when every model is out."""
    provider = provider or llm.get(task.provider); limit = min(limit or MAX_ROWS, MAX_ROWS)
    todo = task.items(in_dir, out_dir, again); log('%d %s items without a draft; drafting %d' % (len(todo), task.name, min(limit, len(todo))))
    n = dict(accepted=0, rejected=0, skipped=0, stopped=False, tokens_in=0, tokens_out=0); last = 0.0
    for it in todo[:limit]:
        if chain.exhausted: break
        wait = last + gap - clock()
        if wait > 0: sleep(wait)
        r = llm.complete(provider, chain, task.system, it.text, task.schema, key, task.temperature, task.max_out, log=log); last = clock()
        if r.get('error') == 'no model left': break
        if 'error' in r: n['skipped'] += 1; log('%s %s: %s %s' % (it.id, 'skipped' if r['error'] == 'busy' else 'error', r['error'], r.get('detail', ''))); continue
        t = r.get('tokens', {}); n['tokens_in'] += t.get('promptTokenCount', 0); n['tokens_out'] += t.get('candidatesTokenCount', 0)
        why = task.check(r['answer'], it.source)
        rec = {k: (v.strip() if isinstance(v, str) else v) for k, v in r['answer'].items()}   # the answer's own fields first; the run's fields below win on a clash
        rec.update(id=it.id, name=it.name, model=r['model'], prompt=task.prompt_version, tokens=t, at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'))
        if why: rec['rejected'] = why; write(os.path.join(out_dir, 'rejected', it.id + '.json'), rec); n['rejected'] += 1
        else: write(os.path.join(out_dir, it.id + '.json'), rec); n['accepted'] += 1
        log('%s -> %s' % (it.id, 'REJECTED: ' + why if why else 'ok'))
    n['stopped'] = chain.exhausted
    if n['stopped']: log('STOP: every model is out (%s). Drafts so far are kept; run again later.' % ', '.join(chain.out_of))
    task.review(out_dir)
    log('accepted %d | rejected %d | skipped %d | prompt tokens %d | output tokens %d' % (n['accepted'], n['rejected'], n['skipped'], n['tokens_in'], n['tokens_out']))
    return n

class Stories(Task):
    """The story and why-it-matters drafts (#196, #747): the prompt, schema, checks and review pages are the ones in gemini_stories.py, which stays the reference."""
    name = 'stories'
    def __init__(self):
        import gemini_stories as g; self.g = g
        self.system, self.schema, self.prompt_version, self.max_out = g.SYSTEM, g.SCHEMA, g.PROMPT_VERSION, g.MAX_OUT
    def items(self, in_dir, out_dir, again):
        out = []
        for pid, name, where, kind in self.g.todo(in_dir, out_dir, again):
            src = open(os.path.join(in_dir, 'research', pid + '.md'), encoding='utf-8').read()
            out.append(Item(pid, name, 'PLACE: %s (%s; %s)\n\nSOURCE TEXT:\n%s' % (name, where, kind, src[:self.g.RESEARCH_CHARS]), src))
        return out
    def check(self, answer, source): return self.g.check(answer, source)
    def review(self, out_dir): self.g.review(out_dir)

TASKS = {'stories': Stories}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    if len(args) < 3 or args[0] not in TASKS: print(__doc__); sys.exit(2)
    task = TASKS[args[0]](); limit = int(args[3]) if len(args) > 3 else 15
    provider = llm.get(task.provider)
    try: chain = llm.chain_for(provider, os.environ.get('GEMINI_MODEL') or provider.models[0])
    except ValueError as e: print(e); sys.exit(2)
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key: print('GEMINI_API_KEY is not set'); sys.exit(2)
    run(task, args[1], args[2], limit, again, chain, key, provider)

if __name__ == '__main__': main()
