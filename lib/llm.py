"""llm.py: one interface for the pipeline's model calls (#779 step a). A task asks for `complete(...)`; which provider and model answer is a setting, not code in the task.
What it gives: Provider (the base: a name, an allowlist of models and generate()), GeminiProvider (the adapter over lib/gemini_api.py, which keeps the HTTP, retry and quota code),
register()/get() to look a provider up by name, Chain (the model list that hands over, shared with gemini_api) and complete() (one item through a chain: a model out of quota is
dropped and the next one takes the same item; a model that stays busy for MAX_BUSY_IN_A_ROW items in a row is dropped too).
QuotaStop and Overloaded are the same classes as in gemini_api, so a job that catches either name keeps working. A new provider is one subclass plus register(); its host must be in
lib/allowed_sources.json and its calls must go through lib/fetch.py (owner-merged files). Nothing here prints or writes a key.
Result of complete(): {'answer', 'tokens', 'model'} on success, {'error', ...} for a bad answer (the model is still in), {'error': 'no model left'} when the chain is exhausted."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemini_api
from gemini_api import Chain, QuotaStop, Overloaded, MAX_BUSY_IN_A_ROW

class Provider:
    """A model provider. models: the names a task may ask for (the allowlist). generate() returns {'answer', 'tokens'} or {'error'} and may raise QuotaStop or Overloaded."""
    name = ''
    models = ()
    def generate(self, model, system, text, schema, key, temperature=0, max_out=600, **kw):
        raise NotImplementedError

class GeminiProvider(Provider):
    name = 'gemini'
    models = ('gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-3.8-flash')   # the same list as jobs/gemini_stories.py MODELS; a later step makes the jobs read it from here
    def generate(self, model, system, text, schema, key, temperature=0, max_out=600, **kw):
        return gemini_api.generate(model, gemini_api.request_body(system, text, schema, temperature, max_out), key, **kw)

PROVIDERS = {}
def register(p):
    PROVIDERS[p.name] = p; return p
def get(name):
    if name not in PROVIDERS: raise ValueError('provider %r is not one of %s' % (name, ', '.join(sorted(PROVIDERS))))
    return PROVIDERS[name]
register(GeminiProvider())

def chain_for(provider, names):
    """A Chain over the provider's allowlist (an unknown model name raises ValueError)."""
    return Chain(names, provider.models)

def complete(provider, chain, system, text, schema, key, temperature=0, max_out=600, log=None, **kw):
    """One item through the chain (see the module doc). log: an optional function that gets the 'MODEL OUT' lines."""
    say = log or (lambda s: None)
    while not chain.exhausted:
        try:
            r = provider.generate(chain.current, system, text, schema, key, temperature, max_out, **kw)
        except QuotaStop as e:
            say(chain.out(str(e))); continue
        except Overloaded as e:
            chain.busy_row += 1
            if chain.busy_row >= MAX_BUSY_IN_A_ROW: say(chain.out('busy %d items in a row (%s)' % (chain.busy_row, e))); continue
            return {'error': 'busy', 'model': chain.current}
        chain.busy_row = 0
        r['model'] = chain.current
        return r
    return {'error': 'no model left'}
