#!/usr/bin/env python3
"""gemini_batch.py: a small, capped trial of the Gemini API as a batch inference backend (#747).
Usage: gemini_batch.py [out.json]
Reads five journeys (title, text, 'when'), asks Gemini in which calendar months each journey is under way (the idea of #740), validates the
answers and writes them with token counts to out.json (default gemini-trial.json). It changes no data file and opens no pull request: the trial
only shows whether the key, the host, the model and the output format work, what it costs and how good the answers are.
The key comes from the environment (GEMINI_API_KEY), is sent only in a request header and is never printed or written.
All traffic goes through lib/fetch.py (host generativelanguage.googleapis.com must be in lib/allowed_sources.json). Hard caps: MAX_ROWS rows, MAX_OUT tokens per row."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import fetch
import gemini_api as api   # the shared calling code (lib/gemini_api.py, #772)
MODEL = 'gemini-3.5-flash-lite'
JOURNEYS = ['monarch', 'sockeye', 'caribouwest', 'osprey', 'altiplano']
MAX_ROWS = 5; MAX_OUT = 400
PROMPT = ('You read the text of an animal journey and say in which calendar months (1 = January to 12 = December) the journey is under way. '
          'Use only the text given. If the text gives no season, return an empty list and set "basis" to "no season in the text". '
          'Reply as JSON: {"months": [integers 1-12], "basis": "one short sentence quoting or paraphrasing the text"}.\n\nTitle: %s\nText: %s\nWhen: %s')
SCHEMA = {'type': 'OBJECT', 'properties': {'months': {'type': 'ARRAY', 'items': {'type': 'INTEGER'}}, 'basis': {'type': 'STRING'}}, 'required': ['months', 'basis']}

def load(jid, data_dir=None):
    j = json.load(open(os.path.join(data_dir or os.path.join(ROOT, 'data', 'journeys'), jid + '.json')))
    return dict(id=jid, title=j.get('title', ''), text=j.get('text', ''), when=j.get('when', ''))

def ask(row, key):
    body = api.request_body(None, PROMPT % (row['title'], row['text'], row['when']), SCHEMA, temperature=0, max_out=MAX_OUT)
    try:
        return api.generate(MODEL, body, key, timeout=60, busy_waits=())   # the trial does not retry a busy answer: it only shows whether the key and model work
    except api.QuotaStop: return dict(error='HTTP 429')
    except api.Overloaded as e: return dict(error=str(e))

def valid(ans):
    """None when the answer is usable, else the reason."""
    m = ans.get('months')
    if not isinstance(m, list) or any(not isinstance(x, int) or not 1 <= x <= 12 for x in m): return 'months must be a list of integers 1-12'
    if not str(ans.get('basis', '')).strip(): return 'basis missing'
    return None

def main():
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key: print('GEMINI_API_KEY is not set'); sys.exit(2)
    out_path = sys.argv[1] if len(sys.argv) > 1 else 'gemini-trial.json'
    results = []; tin = tout = 0
    for jid in JOURNEYS[:MAX_ROWS]:
        row = load(jid); r = ask(row, key); r['id'] = jid; r['title'] = row['title']
        if 'answer' in r:
            r['problem'] = valid(r['answer']); t = r['tokens']; tin += t.get('promptTokenCount', 0); tout += t.get('candidatesTokenCount', 0)
        results.append(r)
        print(jid, '->', r.get('answer') or r.get('error'), '| problem:', r.get('problem'), flush=True)
    json.dump(dict(model=MODEL, rows=results, prompt_tokens=tin, output_tokens=tout), open(out_path, 'w'), indent=1)
    print('model', MODEL, '| prompt tokens', tin, '| output tokens', tout)
    if any('error' in r for r in results): sys.exit(1)

if __name__ == '__main__': main()
