"""openverse_api.py: what a place or species picture from Openverse must be (#887). MOVED from the old jobs/openversephotos.py (deleted, #934) so lib/place_sources.py does not reach into jobs/.
SHEET_WORDS (the herbarium and museum words) lives here; lib/species_sources.py imports it, so the GBIF and Openverse rules share one list."""
import re

SHEET_WORDS = ('herbari', 'specimen', 'nmnh', 'extant biology', 'iiif', 'museum', 'collections.')   # records of herbaria and museums, even when GBIF labels them as observations
API = 'https://api.openverse.org/v1/images/'
# Openverse's licence codes -> (short name, licence link). Never NC or ND.
LICENCES = {('cc0', ''): ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'), ('pdm', ''): ('Public domain', 'https://creativecommons.org/publicdomain/mark/1.0'),
            ('by', None): ('CC BY', 'https://creativecommons.org/licenses/by/%s'), ('by-sa', None): ('CC BY-SA', 'https://creativecommons.org/licenses/by-sa/%s')}
BAD_PROVIDERS = ('inaturalist',)
def licence_of(r):
    """(short name with version, https licence link) for a result under CC0, PDM, CC BY or CC BY-SA, else None."""
    code = (r.get('license') or '').lower().strip(); ver = (r.get('license_version') or '').strip()
    if code in ('cc0', 'pdm'): name, link = LICENCES[(code, '')]; return (name, link)
    if code in ('by', 'by-sa') and re.fullmatch(r'\d\.\d', ver):
        name, link = LICENCES[(code, None)]; return ('%s %s' % (name, ver), link % ver)
    return None
def norm(s): return ' '.join(re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).split())
def unwanted(r):
    """True for iNaturalist (provider, source, or any link) and for herbarium or museum records."""
    blob = ' '.join(str(r.get(k) or '') for k in ('provider', 'source', 'foreign_landing_url', 'url', 'title', 'category', 'attribution')).lower()
    return any(b in blob for b in BAD_PROVIDERS) or any(w in blob for w in SHEET_WORDS) or 'herbarium' in blob
