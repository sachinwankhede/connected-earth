"""gemini_api.py: the shared Gemini API calling code for the manual data-gemini-* jobs (#772). Rules, limits and lessons: docs/GEMINI-API.md.
What it gives a task: generate() (one request with the retry and quota handling below), Chain (the model list that hands over when a model is out of quota or busy),
request_body() (system prompt, user text, JSON schema, temperature, token cap) and the errors QuotaStop and Overloaded. A task supplies only its prompt, schema and checks.
The key is sent only in the x-goog-api-key header and is never printed or written. All traffic goes through lib/fetch.py (host generativelanguage.googleapis.com is in lib/allowed_sources.json).
Error model: a 429 whose retry delay is at most MAX_WAIT seconds is waited for once; a longer delay (a daily limit) raises QuotaStop. A 500, 503, 504 or a timeout is retried after each of
BUSY_WAITS seconds, then raises Overloaded. Any other HTTP error comes back as {'error': 'HTTP <code>', 'detail': ...}; an answer that is not JSON as {'error': 'unreadable answer'}."""
import os, re, sys, json, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch

URL = 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'
GAP = 15                      # seconds between two requests (free tier: 5 to 15 requests a minute)
MAX_WAIT = 90                 # longest 429 retry delay that is waited for
BUSY_WAITS = (30, 90, 180)    # seconds to wait before each retry of a 500, 503, 504 or timeout
MAX_BUSY_IN_A_ROW = 3         # items in a row that stay busy: the model is marked out

class QuotaStop(Exception): pass
class Overloaded(Exception): pass

def retry_delay(body):
    """Seconds Google asks us to wait (from the 429 body); an hour when the message gives none."""
    m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', body.decode('utf-8', 'replace') if isinstance(body, bytes) else str(body))
    return int(float(m.group(1))) + 1 if m else 3600

def request_body(system, text, schema, temperature=0, max_out=600):
    """The request: an optional system prompt, the user text, JSON output in the given schema."""
    b = {'contents': [{'parts': [{'text': text}]}],
         'generationConfig': {'temperature': temperature, 'maxOutputTokens': max_out, 'responseMimeType': 'application/json', 'responseSchema': schema}}
    if system: b['systemInstruction'] = {'parts': [{'text': system}]}
    return b

def generate(model, body, key, timeout=120, busy_waits=None):
    """One request (busy_waits: seconds before each retry of a 500, 503, 504 or timeout; default BUSY_WAITS, () for none). Returns {'answer': <parsed JSON>, 'tokens': usageMetadata} or {'error': ...}; raises QuotaStop or Overloaded (see the module doc)."""
    req = urllib.request.Request(URL % model, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': key}, method='POST')
    waits = BUSY_WAITS if busy_waits is None else busy_waits
    attempt = busy = 0
    while True:
        try:
            j = json.loads(fetch.urlopen(req, timeout=timeout).read()); break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = retry_delay(e.read())
                if attempt == 0 and wait <= MAX_WAIT: attempt = 1; time.sleep(wait + 2); continue
                raise QuotaStop('HTTP 429, retry in %ss' % wait)
            if e.code in (500, 503, 504) and busy < len(waits): time.sleep(waits[busy]); busy += 1; continue
            if e.code in (500, 503, 504): raise Overloaded('HTTP %d' % e.code)
            return dict(error='HTTP %d' % e.code, detail=e.read()[:200].decode('utf-8', 'replace'))
        except Exception as e:
            if busy < len(waits): time.sleep(waits[busy]); busy += 1; continue
            raise Overloaded(type(e).__name__)
    try:
        return dict(answer=json.loads(j['candidates'][0]['content']['parts'][0]['text']), tokens=j.get('usageMetadata', {}))
    except Exception:
        return dict(error='unreadable answer')

class Chain:
    """The models to try, in order. A model that is out of quota or stays busy is out for the run and the next one takes the same item.
    names: a comma list or a list; allowed: the allowlist (an unknown name raises ValueError)."""
    def __init__(self, names, allowed):
        self.names = [m.strip() for m in (names.split(',') if isinstance(names, str) else names) if m.strip()]
        bad = [m for m in self.names if m not in allowed]
        if not self.names or bad: raise ValueError('model %r is not one of %s' % (', '.join(bad) or names, ', '.join(allowed)))
        self.idx = 0; self.busy_row = 0; self.out_of = []
    @property
    def exhausted(self): return self.idx >= len(self.names)
    @property
    def current(self): return self.names[self.idx]
    def out(self, why):
        """Mark the current model out; returns the log line. The busy count starts again for the next model."""
        self.out_of.append(self.current); nxt = '' if self.idx + 1 >= len(self.names) else '; trying ' + self.names[self.idx + 1]
        line = 'MODEL OUT: %s (%s)%s' % (self.current, why, nxt); self.idx += 1; self.busy_row = 0; return line
